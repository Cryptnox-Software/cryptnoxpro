import types
import argparse

import pytest


def make_mock_cryptnoxpy(mode=None):
    mock = types.SimpleNamespace()

    class Exceptions:
        class SeedException(Exception):
            pass

        class ReadPublicKeyException(Exception):
            pass

        class PukException(Exception):
            def __init__(self, message="PUK error", number_of_retries=0):
                super().__init__(message)
                self.number_of_retries = number_of_retries

    class KeyTypeMapping:
        class _K:
            name = "K1"

        class _R:
            name = "R1"

        K1 = _K()
        R1 = _R()

        def __getitem__(self, key):
            if isinstance(mode, Exception):
                raise mode
            if mode == "seed":
                raise Exceptions.SeedException()
            if mode == "rpk":
                raise Exceptions.ReadPublicKeyException("bad key")
            k = key.upper()
            if k == "K1":
                return self.K1
            if k == "R1":
                return self.R1
            raise KeyError(key)

    class Derivation:
        CURRENT_KEY = "CURRENT_KEY"

    mock.exceptions = Exceptions
    mock.KeyType = KeyTypeMapping()
    mock.Derivation = Derivation
    return mock


def ns(**kwargs):
    return argparse.Namespace(**kwargs)


def make_card(pubkey_bytes=b"\x02" + b"\x11" * 32, *,
              derive_side_effect=None,
              get_clear_side_effect=None,
              set_export_side_effect=None):
    class Card:
        open = True
        valid_key = True
        pin_authentication = False
        info = {}

        def set_clearpubkey(self, enable, puk):
            if set_export_side_effect:
                raise set_export_side_effect
            return True

        def derive(self, key_type, path):
            if derive_side_effect:
                raise derive_side_effect
            return True

        def get_public_key_clear(self, derivation, path, compressed):
            if get_clear_side_effect:
                raise get_clear_side_effect
            return pubkey_bytes

    return Card()


def test_meets_condition_true_false():
    from cryptnoxpro.command.get_clearpubkey import GetClearpubkey
    assert GetClearpubkey.meets_condition(ns(command="get_clearpubkey")) is True
    assert GetClearpubkey.meets_condition(ns(command="other")) is False


def test_cli_defaults_parse():
    from cryptnoxpro import main
    parser = main.get_parser()
    args = parser.parse_args(["get_clearpubkey"])  # defaults only
    assert args.command == "get_clearpubkey"
    assert args.key_type == "K1"
    assert args.puk == ""
    assert args.path == ""
    assert args.compressed is True


def test_success_k1_default_current_key_compressed(monkeypatch, capsys):
    from cryptnoxpro.command import get_clearpubkey as mod
    monkeypatch.setattr(mod, "cryptnoxpy", make_mock_cryptnoxpy(), raising=True)

    cmd = mod.GetClearpubkey(ns(command="get_clearpubkey", key_type="K1", puk="", path="", compressed=True, uncompressed=False))
    ret = cmd._execute(make_card())
    out = capsys.readouterr().out
    assert ret == 0
    assert "Getting clear public key from card" in out
    assert "Compressed: True" in out
    assert "Clear Public Key Retrieved" in out
    assert "Format: Compressed" in out


def test_success_with_puk_enables_export(monkeypatch, capsys):
    from cryptnoxpro.command import get_clearpubkey as mod
    monkeypatch.setattr(mod, "cryptnoxpy", make_mock_cryptnoxpy(), raising=True)

    calls = {}

    class Card:
        open = True
        valid_key = True
        pin_authentication = False
        info = {}
        def set_clearpubkey(self, enable, puk):
            calls["puk"] = puk
            return True
        def derive(self, key_type, path):
            return True
        def get_public_key_clear(self, derivation, path, compressed):
            return b"\x02" + b"\x22" * 32

    ret = mod.GetClearpubkey(ns(command="get_clearpubkey", key_type="K1", puk="112233", path="", compressed=True, uncompressed=False))._execute(Card())
    out = capsys.readouterr().out
    assert ret == 0
    assert "Enabling clear pubkey reading capability" in out
    assert calls["puk"] == "112233"


def test_with_path_and_derive_failure_then_continue(monkeypatch, capsys):
    from cryptnoxpro.command import get_clearpubkey as mod
    monkeypatch.setattr(mod, "cryptnoxpy", make_mock_cryptnoxpy(), raising=True)

    card = make_card(pubkey_bytes=b"\x02" + b"\x33" * 32, derive_side_effect=RuntimeError("d"))
    ret = mod.GetClearpubkey(ns(command="get_clearpubkey", key_type="K1", puk="", path="m/0'", compressed=True, uncompressed=False))._execute(card)
    out = capsys.readouterr().out
    assert ret == 0
    assert "Path: m/0'" in out
    assert "Format: Compressed" in out


def test_uncompressed_and_xonly_formats(monkeypatch, capsys):
    from cryptnoxpro.command import get_clearpubkey as mod
    monkeypatch.setattr(mod, "cryptnoxpy", make_mock_cryptnoxpy(), raising=True)

    # Uncompressed 65 bytes
    ret = mod.GetClearpubkey(ns(command="get_clearpubkey", key_type="K1", puk="", path="", compressed=False, uncompressed=True))._execute(
        make_card(pubkey_bytes=b"\x04" + b"\x55" * 64)
    )
    out = capsys.readouterr().out
    assert ret == 0
    assert "Format: Uncompressed (65 bytes)" in out

    # X-only 32 bytes
    ret = mod.GetClearpubkey(ns(command="get_clearpubkey", key_type="K1", puk="", path="", compressed=True, uncompressed=False))._execute(
        make_card(pubkey_bytes=b"\x77" * 32)
    )
    out = capsys.readouterr().out
    assert ret == 0
    assert "Format: X-coordinate only (32 bytes)" in out


def test_enable_clearpub_puk_exception(monkeypatch, capsys):
    from cryptnoxpro.command import get_clearpubkey as mod
    mock = make_mock_cryptnoxpy()
    monkeypatch.setattr(mod, "cryptnoxpy", mock, raising=True)

    err = mock.exceptions.PukException("bad puk", number_of_retries=1)
    ret = mod.GetClearpubkey(ns(command="get_clearpubkey", key_type="K1", puk="112233", path="", compressed=True, uncompressed=False))._execute(
        make_card(set_export_side_effect=err)
    )
    out = capsys.readouterr().out
    assert ret == -1
    assert "Error: Invalid PUK code" in out


def test_enable_clearpub_other_exception(monkeypatch, capsys):
    from cryptnoxpro.command import get_clearpubkey as mod
    monkeypatch.setattr(mod, "cryptnoxpy", make_mock_cryptnoxpy(), raising=True)

    ret = mod.GetClearpubkey(ns(command="get_clearpubkey", key_type="K1", puk="112233", path="", compressed=True, uncompressed=False))._execute(
        make_card(set_export_side_effect=RuntimeError("oops"))
    )
    out = capsys.readouterr().out
    assert ret == -1
    assert "Error enabling clear pubkey capability: oops" in out


def test_get_clearpubkey_read_exception_mapped_messages(monkeypatch, capsys):
    from cryptnoxpro.command import get_clearpubkey as mod
    mock = make_mock_cryptnoxpy()
    monkeypatch.setattr(mod, "cryptnoxpy", mock, raising=True)

    # 6A88 path
    ret = mod.GetClearpubkey(ns(command="get_clearpubkey", key_type="K1", puk="", path="", compressed=True, uncompressed=False))._execute(
        make_card(get_clear_side_effect=mock.exceptions.ReadPublicKeyException("6A88"))
    )
    out = capsys.readouterr().out
    assert ret == -1
    assert "capability not enabled" in out

    # 6985 path
    ret = mod.GetClearpubkey(ns(command="get_clearpubkey", key_type="K1", puk="", path="", compressed=True, uncompressed=False))._execute(
        make_card(get_clear_side_effect=mock.exceptions.ReadPublicKeyException("6985"))
    )
    out = capsys.readouterr().out
    assert ret == -1
    assert "No seed loaded or PIN not verified" in out

    # X-only uncompressed request message
    ret = mod.GetClearpubkey(ns(command="get_clearpubkey", key_type="K1", puk="", path="", compressed=False, uncompressed=True))._execute(
        make_card(get_clear_side_effect=mock.exceptions.ReadPublicKeyException("X-coordinate ... uncompressed"))
    )
    out = capsys.readouterr().out
    assert ret == -1
    assert "Cannot get uncompressed public key" in out

    # generic read error
    ret = mod.GetClearpubkey(ns(command="get_clearpubkey", key_type="K1", puk="", path="", compressed=True, uncompressed=False))._execute(
        make_card(get_clear_side_effect=mock.exceptions.ReadPublicKeyException("other"))
    )
    out = capsys.readouterr().out
    assert ret == -1
    assert "Error reading clear public key: other" in out


def test_unexpected_in_inner(monkeypatch, capsys):
    from cryptnoxpro.command import get_clearpubkey as mod
    monkeypatch.setattr(mod, "cryptnoxpy", make_mock_cryptnoxpy(), raising=True)
    ret = mod.GetClearpubkey(ns(command="get_clearpubkey", key_type="K1", puk="", path="", compressed=True, uncompressed=False))._execute(
        make_card(get_clear_side_effect=RuntimeError("weird"))
    )
    out = capsys.readouterr().out
    assert ret == -1
    assert "Unexpected error: weird" in out


def test_outer_seed_exception(monkeypatch, capsys):
    from cryptnoxpro.command import get_clearpubkey as mod
    monkeypatch.setattr(mod, "cryptnoxpy", make_mock_cryptnoxpy("seed"), raising=True)
    ret = mod.GetClearpubkey(ns(command="get_clearpubkey", key_type="K1", puk="", path="", compressed=True, uncompressed=False))._execute(
        make_card()
    )
    out = capsys.readouterr().out
    assert ret == -1
    assert "No seed exists on the card" in out


def test_outer_unexpected(monkeypatch, capsys):
    from cryptnoxpro.command import get_clearpubkey as mod
    # cause KeyType mapping to raise generic
    monkeypatch.setattr(mod, "cryptnoxpy", make_mock_cryptnoxpy(mode=RuntimeError("boom")), raising=True)
    ret = mod.GetClearpubkey(ns(command="get_clearpubkey", key_type="K1", puk="", path="", compressed=True, uncompressed=False))._execute(
        make_card()
    )
    out = capsys.readouterr().out
    assert ret == -1
    assert "Unexpected error: boom" in out

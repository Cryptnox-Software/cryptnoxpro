import types
import argparse

import pytest


def make_mock_cryptnoxpy(raise_in_keytype=None):
    mock = types.SimpleNamespace()

    class Exceptions:
        class SeedException(Exception):
            pass

        class ReadPublicKeyException(Exception):
            pass

    class KeyTypeMapping:
        K1 = "K1"
        R1 = "R1"

        def __getitem__(self, key):
            if isinstance(raise_in_keytype, Exception):
                raise raise_in_keytype
            if raise_in_keytype == "seed":
                raise Exceptions.SeedException()
            if raise_in_keytype == "rpk":
                raise Exceptions.ReadPublicKeyException("bad key")
            k = key.upper()
            if k == "K1":
                return self.K1
            if k == "R1":
                return self.R1
            raise KeyError(key)

    mock.exceptions = Exceptions
    mock.KeyType = KeyTypeMapping()
    return mock


def make_namespace(**kwargs):
    ns = argparse.Namespace(**kwargs)
    return ns


def make_card(get_xpub_ret="xpub", side_effect=None):
    class Card:
        serial_number = 123
        open = True
        valid_key = True
        pin_authentication = False
        info = {}

        def get_public_key_extended(self, key_type, puk):
            if side_effect:
                raise side_effect
            return get_xpub_ret

    return Card()


def test_meets_condition_true_false(monkeypatch):
    from cryptnoxpro.command.get_xpub import getXpub

    assert getXpub.meets_condition(make_namespace(command="get_xpub")) is True
    assert getXpub.meets_condition(make_namespace(command="other")) is False


def test_add_options_parsing_defaults():
    from cryptnoxpro.command.options import options
    from cryptnoxpro import main

    parser = main.get_parser()
    # options.add already called in get_parser(); don't call again to avoid duplicate subparsers
    args = parser.parse_args(["get_xpub"])  # defaults

    assert getattr(args, "command") == "get_xpub"
    assert getattr(args, "key_type") == "K1"
    assert getattr(args, "puk") == ""


def test_execute_k1_success_no_puk(monkeypatch, capsys):
    from cryptnoxpro.command import get_xpub as gx

    # use working mock cryptnoxpy
    monkeypatch.setattr(gx, "cryptnoxpy", make_mock_cryptnoxpy(), raising=True)

    cmd = gx.getXpub(make_namespace(command="get_xpub", key_type="K1", puk=""))
    ret = cmd._execute(make_card(get_xpub_ret="xpub123"))

    out = capsys.readouterr().out
    assert ret == 0
    assert "Getting extended public key for K1 key" in out
    assert "K1 Extended Public Key" in out
    assert "xpub123" in out


def test_execute_k1_success_with_puk(monkeypatch, capsys):
    from cryptnoxpro.command import get_xpub as gx

    calls = {}

    class Card:
        open = True
        valid_key = True
        pin_authentication = False
        info = {}
        def get_public_key_extended(self, key_type, puk):
            calls["args"] = (key_type, puk)
            return "XPUB_WITH_PUK"

    monkeypatch.setattr(gx, "cryptnoxpy", make_mock_cryptnoxpy(), raising=True)

    cmd = gx.getXpub(make_namespace(command="get_xpub", key_type="K1", puk="112233"))
    ret = cmd._execute(Card())

    out = capsys.readouterr().out
    assert ret == 0
    assert "Enabling clear pubkey reading capability" in out
    assert calls["args"][1] == "112233"
    assert "XPUB_WITH_PUK" in out


def test_execute_k1_inner_exception(monkeypatch, capsys):
    from cryptnoxpro.command import get_xpub as gx

    monkeypatch.setattr(gx, "cryptnoxpy", make_mock_cryptnoxpy(), raising=True)

    cmd = gx.getXpub(make_namespace(command="get_xpub", key_type="K1", puk=""))
    ret = cmd._execute(make_card(side_effect=Exception("boom")))

    out = capsys.readouterr().out
    assert ret == -1
    assert "Error getting K1 public key: boom" in out


def test_execute_r1_path(monkeypatch, capsys):
    from cryptnoxpro.command import get_xpub as gx

    mock = make_mock_cryptnoxpy()
    # Force mapping to R1 for the string
    monkeypatch.setattr(gx, "cryptnoxpy", mock, raising=True)

    cmd = gx.getXpub(make_namespace(command="get_xpub", key_type="R1", puk=""))
    ret = cmd._execute(make_card())

    out = capsys.readouterr().out
    assert ret == 0
    assert "Cannot get extended public key for R1 key." in out


def test_outer_seed_exception_branch(monkeypatch, capsys):
    from cryptnoxpro.command import get_xpub as gx

    mock = make_mock_cryptnoxpy("seed")
    monkeypatch.setattr(gx, "cryptnoxpy", mock, raising=True)

    cmd = gx.getXpub(make_namespace(command="get_xpub", key_type="K1", puk=""))
    ret = cmd._execute(make_card())

    out = capsys.readouterr().out
    assert ret == -1
    assert "No seed exists on the card" in out


def test_outer_read_public_key_exception_branch(monkeypatch, capsys):
    from cryptnoxpro.command import get_xpub as gx

    mock = make_mock_cryptnoxpy("rpk")
    monkeypatch.setattr(gx, "cryptnoxpy", mock, raising=True)

    cmd = gx.getXpub(make_namespace(command="get_xpub", key_type="K1", puk=""))
    ret = cmd._execute(make_card())

    out = capsys.readouterr().out
    assert ret == -1
    assert "Error reading public key: bad key" in out


def test_outer_unexpected_exception_branch(monkeypatch, capsys):
    from cryptnoxpro.command import get_xpub as gx

    # Raise a generic exception during KeyType mapping
    mock = make_mock_cryptnoxpy(raise_in_keytype=RuntimeError("weird"))
    monkeypatch.setattr(gx, "cryptnoxpy", mock, raising=True)

    cmd = gx.getXpub(make_namespace(command="get_xpub", key_type="K1", puk=""))
    ret = cmd._execute(make_card())

    out = capsys.readouterr().out
    assert ret == -1
    assert "Unexpected error: weird" in out

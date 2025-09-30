import argparse
import types

import pytest


def ns(**kwargs):
    return argparse.Namespace(**kwargs)


def make_mock_cryptnoxpy():
    mock = types.SimpleNamespace()

    class Exceptions:
        class SeedException(Exception):
            pass

        class PinException(Exception):
            def __init__(self, msg="pin", number_of_retries=0):
                super().__init__(msg)
                self.number_of_retries = number_of_retries

        class DataValidationException(Exception):
            pass

        class SecureChannelException(Exception):
            pass

    mock.exceptions = Exceptions
    return mock


def make_card_mock(*, verify_pin_side_effect=None, decrypt_side_effect=None, decrypt_return=b"\xAA" * 32):
    class Card:
        serial_number = 111
        initialized = True
        valid_key = True
        seed_source = "INTERNAL"

        def verify_pin(self, pin):
            if verify_pin_side_effect:
                raise verify_pin_side_effect
            return True

        def decrypt(self, **kwargs):
            if decrypt_side_effect:
                raise decrypt_side_effect
            return decrypt_return

    return Card()


def valid_uncompressed_pubkey_hex():
    return (b"\x04" + b"\x11" * 64).hex()


def test_meets_condition_true_false():
    from cryptnoxpro.command.decrypt import Decrypt
    assert Decrypt.meets_condition(ns(command="decrypt")) is True
    assert Decrypt.meets_condition(ns(command="other")) is False


def test_cli_defaults_parse():
    from cryptnoxpro import main
    parser = main.get_parser()
    args = parser.parse_args(["decrypt"])  # defaults
    assert args.command == "decrypt"
    assert args.mode == "symmetric"
    assert getattr(args, "pubkey") is None
    assert args.data == ""
    assert args.pin == ""


def test_error_when_cryptnoxpy_missing(monkeypatch, capsys):
    from cryptnoxpro.command import decrypt as mod
    monkeypatch.setattr(mod, "cryptnoxpy", None, raising=True)
    ret = mod.Decrypt(ns(command="decrypt"))._execute(make_card_mock())
    out = capsys.readouterr().out
    assert ret == -1
    assert "cryptnoxpy library is not available" in out


def test_error_when_card_missing_decrypt(capsys):
    from cryptnoxpro.command import decrypt as mod
    class Card:
        serial_number = 1
        initialized = True
        valid_key = True
        seed_source = "INTERNAL"
    ret = mod.Decrypt(ns(command="decrypt"))._execute(Card())
    out = capsys.readouterr().out
    assert ret == -1
    assert "does not support decrypt" in out


def test_pin_auth_success_and_symmetric_success(monkeypatch, capsys):
    from cryptnoxpro.command import decrypt as mod
    monkeypatch.setattr(mod, "cryptnoxpy", make_mock_cryptnoxpy(), raising=True)
    card = make_card_mock()
    # Provide a valid pubkey to skip ephemeral generation branch verification
    ret = mod.Decrypt(ns(command="decrypt", mode="symmetric", pubkey=valid_uncompressed_pubkey_hex(), pin="1234"))._execute(card)
    out = capsys.readouterr().out
    assert ret == 0
    assert "PIN authentication successful" in out
    assert "Mode: Output symmetric key" in out
    assert "Symmetric key generated successfully" in out


def test_pin_auth_failure(monkeypatch, capsys):
    from cryptnoxpro.command import decrypt as mod
    m = make_mock_cryptnoxpy()
    monkeypatch.setattr(mod, "cryptnoxpy", m, raising=True)
    card = make_card_mock(verify_pin_side_effect=Exception("bad pin"))
    ret = mod.Decrypt(ns(command="decrypt", mode="symmetric", pubkey=valid_uncompressed_pubkey_hex(), pin="1234"))._execute(card)
    out = capsys.readouterr().out
    assert ret == -1
    assert "PIN authentication failed" in out


def test_ephemeral_key_generation_success(monkeypatch, capsys):
    from cryptnoxpro.command import decrypt as mod
    monkeypatch.setattr(mod, "cryptnoxpy", make_mock_cryptnoxpy(), raising=True)
    # No pubkey provided triggers ephemeral generation, ensure overall success
    ret = mod.Decrypt(ns(command="decrypt", mode="symmetric", pubkey="", pin=""))._execute(make_card_mock())
    out = capsys.readouterr().out
    assert ret == 0
    assert "Generating ephemeral key pair" in out
    assert "Symmetric key generated successfully" in out


def test_ephemeral_key_generation_failure(monkeypatch, capsys):
    from cryptnoxpro.command import decrypt as mod
    monkeypatch.setattr(mod, "cryptnoxpy", make_mock_cryptnoxpy(), raising=True)
    # Force key generation to fail
    import cryptography.hazmat.primitives.asymmetric.ec as ec
    def _fail(*args, **kwargs):
        raise RuntimeError("genfail")
    monkeypatch.setattr(ec, "generate_private_key", _fail, raising=True)
    ret = mod.Decrypt(ns(command="decrypt", mode="symmetric", pubkey="", pin=""))._execute(make_card_mock())
    out = capsys.readouterr().out
    assert ret == -1
    assert "Failed to generate ephemeral key pair" in out


def test_pubkey_hex_validation_errors(monkeypatch, capsys):
    from cryptnoxpro.command import decrypt as mod
    monkeypatch.setattr(mod, "cryptnoxpy", make_mock_cryptnoxpy(), raising=True)

    # Bad hex
    ret = mod.Decrypt(ns(command="decrypt", mode="symmetric", pubkey="zz", pin=""))._execute(make_card_mock())
    out = capsys.readouterr().out
    assert ret == -1 and "Invalid public key format" in out

    # Wrong length
    ret = mod.Decrypt(ns(command="decrypt", mode="symmetric", pubkey=(b"\x04" + b"\x22" * 10).hex(), pin=""))._execute(make_card_mock())
    out = capsys.readouterr().out
    assert ret == -1 and "must be 65 bytes" in out

    # Wrong prefix
    ret = mod.Decrypt(ns(command="decrypt", mode="symmetric", pubkey=(b"\x02" + b"\x22" * 64).hex(), pin=""))._execute(make_card_mock())
    out = capsys.readouterr().out
    assert ret == -1 and "Expected prefix: 0x04" in out


def test_mode_and_data_validation_errors(monkeypatch, capsys):
    from cryptnoxpro.command import decrypt as mod
    monkeypatch.setattr(mod, "cryptnoxpy", make_mock_cryptnoxpy(), raising=True)
    good_pub = valid_uncompressed_pubkey_hex()

    # Invalid mode
    ret = mod.Decrypt(ns(command="decrypt", mode="wrong", pubkey=good_pub, pin=""))._execute(make_card_mock())
    out = capsys.readouterr().out
    assert ret == -1 and "Invalid mode" in out

    # Data mode missing data
    ret = mod.Decrypt(ns(command="decrypt", mode="data", pubkey=good_pub, data="", pin=""))._execute(make_card_mock())
    out = capsys.readouterr().out
    assert ret == -1 and "Encrypted data is required" in out

    # Data mode bad hex
    ret = mod.Decrypt(ns(command="decrypt", mode="data", pubkey=good_pub, data="zz", pin=""))._execute(make_card_mock())
    out = capsys.readouterr().out
    assert ret == -1 and "Invalid encrypted data format" in out

    # Data mode not multiple of 16
    ret = mod.Decrypt(ns(command="decrypt", mode="data", pubkey=good_pub, data=(b"\x00" * 15).hex(), pin=""))._execute(make_card_mock())
    out = capsys.readouterr().out
    assert ret == -1 and "must be multiple of 16 bytes" in out


def test_pin_validation_errors(monkeypatch, capsys):
    from cryptnoxpro.command import decrypt as mod
    monkeypatch.setattr(mod, "cryptnoxpy", make_mock_cryptnoxpy(), raising=True)
    good_pub = valid_uncompressed_pubkey_hex()

    # Too long
    ret = mod.Decrypt(ns(command="decrypt", mode="symmetric", pubkey=good_pub, pin="1" * 10))._execute(make_card_mock())
    out = capsys.readouterr().out
    assert ret == -1 and "PIN too long" in out

    # Non digits
    ret = mod.Decrypt(ns(command="decrypt", mode="symmetric", pubkey=good_pub, pin="12a"))._execute(make_card_mock())
    out = capsys.readouterr().out
    assert ret == -1 and "PIN must contain only digits" in out


def test_decrypt_symmetric_and_data_success(monkeypatch, capsys):
    from cryptnoxpro.command import decrypt as mod
    monkeypatch.setattr(mod, "cryptnoxpy", make_mock_cryptnoxpy(), raising=True)
    good_pub = valid_uncompressed_pubkey_hex()

    # symmetric
    ret = mod.Decrypt(ns(command="decrypt", mode="symmetric", pubkey=good_pub, pin=""))._execute(make_card_mock(decrypt_return=b"\xBB" * 32))
    out = capsys.readouterr().out
    assert ret == 0 and "Symmetric key generated successfully" in out

    # data
    data_hex = (b"\x00" * 16).hex()
    ret = mod.Decrypt(ns(command="decrypt", mode="data", pubkey=good_pub, data=data_hex, pin=""))._execute(make_card_mock(decrypt_return=b"hello world\x00"))
    out = capsys.readouterr().out
    assert ret == 0 and "Data decrypted successfully" in out and "Decrypted text: hello world" in out


def test_decrypt_exception_branches(monkeypatch, capsys):
    from cryptnoxpro.command import decrypt as mod
    m = make_mock_cryptnoxpy()
    monkeypatch.setattr(mod, "cryptnoxpy", m, raising=True)
    good_pub = valid_uncompressed_pubkey_hex()

    # SeedException
    ret = mod.Decrypt(ns(command="decrypt", mode="symmetric", pubkey=good_pub, pin=""))._execute(
        make_card_mock(decrypt_side_effect=m.exceptions.SeedException())
    )
    out = capsys.readouterr().out
    assert ret == -1 and "No seed/key loaded" in out

    # PinException
    ret = mod.Decrypt(ns(command="decrypt", mode="symmetric", pubkey=good_pub, pin=""))._execute(
        make_card_mock(decrypt_side_effect=m.exceptions.PinException())
    )
    out = capsys.readouterr().out
    assert ret == -1 and "PIN is not correct" in out

    # DataValidationException
    ret = mod.Decrypt(ns(command="decrypt", mode="symmetric", pubkey=good_pub, pin=""))._execute(
        make_card_mock(decrypt_side_effect=m.exceptions.DataValidationException("bad"))
    )
    out = capsys.readouterr().out
    assert ret == -1 and "Data validation failed" in out

    # SecureChannelException
    ret = mod.Decrypt(ns(command="decrypt", mode="symmetric", pubkey=good_pub, pin=""))._execute(
        make_card_mock(decrypt_side_effect=m.exceptions.SecureChannelException("sc"))
    )
    out = capsys.readouterr().out
    assert ret == -1 and "Secure channel communication failed" in out

    # Generic
    ret = mod.Decrypt(ns(command="decrypt", mode="symmetric", pubkey=good_pub, pin=""))._execute(
        make_card_mock(decrypt_side_effect=RuntimeError("oops"))
    )
    out = capsys.readouterr().out
    assert ret == -1 and "Unexpected error: oops" in out

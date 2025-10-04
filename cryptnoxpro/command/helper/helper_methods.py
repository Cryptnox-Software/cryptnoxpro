import ast
from collections.abc import Mapping
from typing import Any

import argparse
import cryptnoxpy

from . import security
from .. import user_keys


def deep_update(source, overrides):
    """
    Update a nested dictionary or similar mapping.
    Modify ``source`` in place.
    """
    for key, value in overrides.items():
        if isinstance(value, Mapping) and value:
            returned = deep_update(source.get(key, {}), value)
            source[key] = returned
        else:
            source[key] = overrides[key]
    return source


class IntRange:
    def __init__(self, imin: int = None, imax: int = None):
        self._imin = imin
        self._imax = imax

    def __call__(self, arg: Any):
        try:
            value = int(arg)
        except ValueError:
            raise self.exception()

        if (self._imin is not None and value < self._imin) or \
                (self._imax is not None and value > self._imax):
            raise self.exception()

        return value

    def exception(self):
        if self._imin is not None and self._imax is not None:
            return argparse.ArgumentTypeError(f"Must be an integer in the range [{self._imin}, "
                                              f"{self._imax}]")
        elif self._imin is not None:
            return argparse.ArgumentTypeError(f"Must be an integer >= {self._imin}")
        elif self._imax is not None:
            return argparse.ArgumentTypeError(f"Must be an integer <= {self._imax}")
        else:
            return argparse.ArgumentTypeError("Must be an integer")


def sign(card: cryptnoxpy.Card, message: bytes,
         derivation: cryptnoxpy.Derivation = cryptnoxpy.Derivation.CURRENT_KEY,
         key_type: cryptnoxpy.KeyType = cryptnoxpy.KeyType.K1, path: str = "",
         filter_eos: bool = False, pin_code: str = "") -> bytes:
    """
    Open the card with a user key or PIN code and sign the given message in the given card

    :param crypnoxpy.Card card: Card to use for signature
    :param bytes message: Message to sign with the card
    :param cryptnoxpy.Derivation derivation: Derivation to use when signing
    :param cryptnoxpy.KeyType key_type: Key type to use when signing
    :param str path: Path to use for signature generation
    :param bool filter_eos: Filter signature to be compatible with eos requirements
    :param str pin_code: If PIN code is given use it instead of asking for it

    :return: Signature of the message generated in the card
    :rtype: bytes
    """
    signature = None

    if user_keys.authenticate(card, message):
        signature = card.sign(message, derivation, key_type, path, filter_eos=filter_eos)

    if not signature:
        if not pin_code:
            pin_code = security.check_pin_code(card)
        signature = card.sign(message, derivation, key_type, path, pin_code, filter_eos)

    if not signature:
        raise ValueError("Error in getting the signature")

    return signature


def try_eval(value: str) -> Any:
    """
    Returns appropriate type for a string

    :param value: Value to evaluate
    :return: Evaluated value
    """
    try:
        value = ast.literal_eval(value)
    except ValueError:
        pass
    return value

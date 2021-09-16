import ast
import collections
from typing import Any, List

import argparse
import cryptnoxpy
from stdiomask import getpass
from tabulate import tabulate

from . import security
from .. import user_keys


class ExitException(Exception):
    """Raised when user has indicated he want's to exit the command"""


def deep_update(source, overrides):
    """
    Update a nested dictionary or similar mapping.
    Modify ``source`` in place.
    """
    for key, value in overrides.items():
        if isinstance(value, collections.Mapping) and value:
            returned = deep_update(source.get(key, {}), value)
            source[key] = returned
        else:
            source[key] = overrides[key]
    return source


def input_with_exit(text, required=True, input_method=None):
    input_method = input_method or input
    while True:
        value = input_method(text).strip()
        if value.lower() == "exit":
            raise ExitException
        if required and not value:
            print("This entry is required")
        else:
            break

    return value


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


def option_input(options: List[str], name: str = ""):
    name = name or "option"
    print(tabulate(enumerate(options, 1)))
    length = len(options)

    while True:
        choice = input_with_exit(f"\nChoose {name} (1 - {length}): ")

        try:
            return options[int(choice) - 1]
        except (IndexError, ValueError):
            print(f"Please, enter a number between 1 and {length}")


def printable_flags(card: cryptnoxpy.Card) -> List[str]:
    flags = []

    if card.initialized:
        flags.append("initialized")
    if card.valid_key:
        try:
            flags.append(f"{card.seed_source.name.lower()} seed")
        except NotImplementedError:
            flags.append("seed")
    if card.pin_authentication:
        flags.append("pin auth")
    if card.pinless_enabled:
        flags.append("pinless")
    if card.extended_public_key:
        flags.append("extended public key")

    keys = []
    for slot_index in cryptnoxpy.SlotIndex:
        try:
            if card.user_key_enabled(slot_index):
                keys.append(slot_index.name.lower())
        except NotImplementedError:
            break
    if keys:
        flags.append(f'user keys: "{", ".join(keys)}"')

    return flags


def sign(card: cryptnoxpy.Card, message: bytes,
         derivation: cryptnoxpy.Derivation = cryptnoxpy.Derivation.CURRENT_KEY,
         key_type: cryptnoxpy.KeyType = cryptnoxpy.KeyType.K1, path: str = "",
         filter_eos: bool = False) -> bytes:
    """
    Open the card with a user key or PIN code and sign the given message in the given card
    
    :param crypnoxpy.Card card: Card to use for signature
    :param bytes message: Message to sign with the card
    :param cryptnoxpy.Derivation derivation: Derivation to use when signing
    :param cryptnoxpy.KeyType key_type: Key type to use when signing
    :param str path: Path to use for signature generation
    :param bool filter_eos: Filter signature to be compatible with eos requirements

    :return: Signature of the message generated in the card
    :rtype: bytes
    """
    signature = None

    if user_keys.authenticate(card, message):
        signature = card.sign(message, derivation, key_type, path, filter_eos=filter_eos)

    if not signature:
        pin_code = security.check_pin_code(card)
        signature = card.sign(message, derivation, key_type, path, pin_code, filter_eos)

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


def secret_with_exit(text, required=True):
    return input_with_exit(text, required, getpass)

def print_warning(text):
    print()
    print(tabulate([[str(text).upper()]], tablefmt="rst"))
    print()

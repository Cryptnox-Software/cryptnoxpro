"""
Module providing user interface components including input validation,
confirmation dialogs, data collection forms, and display formatting
for the command-line interface.
"""

import secrets
import sys
from collections import namedtuple
from typing import List, Union, Dict

import cryptnoxpy
from stdiomask import getpass
from tabulate import tabulate

from . import security

InitData = namedtuple("InitData", ["name", "email", "pin", "puk"])


class ExitException(Exception):
    """Raised when user has indicated he want's to exit the command"""


class StringConvert(str):
    """
    Class for finding if string can be converted to ascii.
    """

    def isascii_(self) -> bool:
        """
        Finding if string can be converted or is ascii.

        :return: Can be or is ascii.
        """
        if sys.version_info[1] == 6:
            try:
                self.encode('ascii')
            except UnicodeEncodeError:
                return False
            else:
                return True
        else:
            return self.isascii()


def confirm(text: str, warning: str = "") -> bool:
    print_warning(warning)

    while True:
        conf = input(f"{text} [y/N] > ")
        if conf.lower() in ("y", "n", ""):
            break
        print('Type "y", "n" or leave empty for no.')

    return conf.lower() == "y"


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


def input_type(text, required=True, type_of_input=str):
    while True:
        try:
            value = input_with_exit(text, required, input)
            return type_of_input(value)
        except ValueError:
            pass


def get_init_data(card: cryptnoxpy.card, easy_mode: bool = False) -> InitData:
    if easy_mode and not confirm("Do you wish to proceed?",
                                 f"WARNING: THIS WILL INITIALIZE THE CARD "
                                 f"IN {security.EASY_MODE_TEXT.upper()}"):
        raise ExitException()

    print("You can enter exit at any point to exit initialisation process.")
    print("Setting Cryptnox parameters\n")

    if easy_mode:
        init_data = InitData(security.EASY_MODE_TEXT.upper(), security.EASY_MODE_TEXT.upper(),
                             security.EASY_MODE_PIN, security.easy_mode_puk(card))
        data = [
            ["Owner's name", ":", init_data.name],
            ["Owner's email", ":", init_data.email],
            [f"Card PIN code ({card.pin_rule})", ":", init_data.pin],
            [f"Card PUK code ({card.puk_rule})", ":", init_data.puk]
        ]
        print(tabulate(data, tablefmt="plain"))
    else:
        init_data = InitData(_get_name(), _get_email(), _get_pin_code(card), _get_puk_code(card))

    return init_data


def option_input(options: Union[Dict[str, str], List[str]], name: str = "", default: str = ""):
    if isinstance(options, list):
        options = {x: x for x in options}
    name = name or "option"
    if default:
        print('Default value is marked with a star, press ENTER to select it.')

    print(tabulate(enumerate([("* " if key == default else "") + value
                              for key, value in options.items()], 1)))
    length = len(options)

    while True:
        choice = input_with_exit(f"\nChoose {name} (1 - {length}): ", not default)
        if choice.lower() == "exit":
            raise ExitException("Exited by user")

        if default and not choice:
            return default

        try:
            return list(options.keys())[int(choice) - 1]
        except (IndexError, ValueError):
            print(f"Please, enter a number between 1 and {length}" +
                  (" or press ENTER for default value" if default else ""))


def print_warning(text):
    if text:
        print()
        print(tabulate([[str(text).upper()]], tablefmt="rst"))
        print()


def secret_with_exit(text, required=True):
    return input_with_exit(text, required, getpass)


def _get_email() -> str:
    return _get_valid_input("Owner's email: ",
                            lambda value: value.isascii_() and len(value) <= 60,
                            "ERROR when input owner email, should be ASCII string no longer than "
                            "60 chars.")


def _get_name() -> str:
    return _get_valid_input("Name: ",
                            lambda text: text.isascii_() and len(text) <= 20,
                            "ERROR when input owner name, should be ASCII string no longer than "
                            "20 chars.")


def _get_pin_code(card: cryptnoxpy.Card) -> str:
    return _verify_input(card, security.get_pin_code, f"Set card PIN code ({card.pin_rule}): ",
                         f"  Repeat PIN code ({card.pin_rule}): ")


def _get_puk_code(card: cryptnoxpy.Card) -> str:
    print(f"For the PUK code: 1) Input your own {card.puk_rule} PUK")
    print("                   2) Generate a random one ")
    puk_choice = input_with_exit("> ")
    while puk_choice not in ["1", "2"]:
        print("Not a valid choice. Please, enter 1 or 2.")
        puk_choice = input_with_exit("> ")

    if puk_choice == "2":
        puk_code = str(secrets.randbelow(10 ** card.PUK_LENGTH)).zfill(card.PUK_LENGTH)
        print("-- Card PUK code : ", puk_code)
        print("-- Save the PUK on a paper for security  --")
    else:
        puk_code = _verify_input(card, security.get_puk_code,
                                 f" Set card PUK code ({card.puk_rule}): ",
                                 f"   Repeat PUK code ({card.puk_rule}): ")

    return puk_code


def _get_valid_input(text: str, valid, error: str = "Invalid value") -> str:
    user_input = StringConvert(input_with_exit(text, required=False))
    while not valid(user_input):
        print(error)
        user_input = StringConvert(input_with_exit(text))

    return user_input


def _verify_input(card: cryptnoxpy.Card, method, text, verify_text,
                  error: str = "The given values are not the same.") -> str:
    while True:
        value = method(card, text)
        verify_value = method(card, verify_text)

        if value == verify_value:
            break

        print(error)

    return value

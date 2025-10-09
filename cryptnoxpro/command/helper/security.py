# -*- coding: utf-8 -*-
"""
Module dealing with security of the application.
"""
import typing
from typing import List, Dict

import cryptnoxpy

from . import ui
from .. import user_keys


class Unauthorized(Exception):
    """
    None of the authorization methods has validated the user.
    """


EASY_MODE_PIN = "000000000"
EASY_MODE_TEXT = "easy mode"


def easy_mode_puk(card):
    return "0" * card.PUK_LENGTH


def check(card, check_seed: bool = True) -> bool:
    """
    Check if card is initialized and pin code is saved.

    :param Card card: Card to use
    :param bool check_seed: If True checks if seed is generated
    :return:
    """
    if card.open:
        return True

    card.check_init()

    if not card.valid_key and check_seed:
        raise cryptnoxpy.exceptions.SeedException("The key is not generated")

    result = False
    try:
        result = user_keys.authenticate(card)
    except NotImplementedError:
        pass

    if not result:
        if card.pin_authentication:
            result = bool(check_pin_code(card))
        else:
            raise Unauthorized("PIN authentication is not allowed.")

    return result


def check_pin_code(card, text: str = "Cryptnox PIN code: ") -> str:
    """
    Check PIN code entered by user against the card on given connection.

    :param Base card: Card to use
    :param str text: Prompt to show to the user

    :return: The entered valid pin code
    :rtype: str
    """

    authorized = False
    pin_code = "1"
    easy_mode = is_easy_mode(card.info)

    while not authorized:
        if easy_mode:
            print("The card is in easy mode, just press ENTER. The PIN will be from easy mode "
                  "regardless of what you type.")

        pin_code = get_pin_code(card, text, [""] if easy_mode else [])

        if easy_mode:
            pin_code = EASY_MODE_PIN

        try:
            authorized = _check_pin_code(card, pin_code, not easy_mode)
        except cryptnoxpy.exceptions.PinException:
            if easy_mode:
                print(f"{EASY_MODE_TEXT} PIN doesn't work. Try other PIN code.\n")
                easy_mode = False
            else:
                raise

    return pin_code


def get_pin_code(card: cryptnoxpy.Card, text: str = "Enter PIN code:",
                 allowed_values: List[str] = None) -> str:
    """
    Get PIN code from the user according to the rules.

    :param Card card: Card to use for PIN code check
    :param str text: Prompt to show to the user
    :param List[str] allowed_values: Valid values besides the those defined
                                     in the rules
    :return: PIN code entered by the user
    :rtype: str
    """
    return _get_code(card.valid_pin, text, allowed_values)


def is_easy_mode(card_info: Dict):
    try:
        return card_info["name"] == card_info["email"] == EASY_MODE_TEXT.upper()
    except TypeError:
        return False


def process_command_with_puk(
        card: cryptnoxpy.Card,
        function: typing.Callable,
        *args,
        **kwargs) -> bool:
    easy_mode = is_easy_mode(card.info)

    while True:
        if easy_mode:
            print(f"The card is in {EASY_MODE_TEXT}, just press ENTER. "
                  f"The PUK will be from {EASY_MODE_TEXT.upper()} regardless of what you type.")

        puk_code = get_puk_code(card, allowed_values=[""] if is_easy_mode else [])
        if easy_mode:
            puk_code = easy_mode_puk(card)

        try:
            result = function(*args, **kwargs, puk=puk_code)
        except cryptnoxpy.exceptions.PukException as error:
            if easy_mode:
                print(f"{EASY_MODE_TEXT} PUK doesn't work. Try other PUK code.\n")
                easy_mode = False
            else:
                if error.number_of_retries > 0:
                    print(f"Wrong PUK code. Remaining retries: {error.number_of_retries} "
                          f"Try again.")
                else:
                    raise
        else:
            break

    return result


def _check_pin_code(card, pin_code, handle_exception: bool = True) -> bool:
    try:
        card.verify_pin(str(pin_code))
    except cryptnoxpy.exceptions.PinException as error:
        if not handle_exception:
            raise error
        number_of_retries = error.number_of_retries
        if number_of_retries == 0:
            raise
        try_str = "tries" if number_of_retries > 1 else "try"
        print(f"Wrong pin code. You have {number_of_retries} {try_str} before the card is locked.")

        return False

    return True


def get_puk_code(card: cryptnoxpy.Card, text: str = "", allowed_values: List = None) -> str:
    """
    Get user input for puk code and check if it is valid.

    :param Card card: Card for use to check PUK code validity
    :param str text: Text displayed to user for value input.
    :param List allowed_values: Values other than 15 digits long strings
    that can be accepted.
    :return: Entered puk code.
    :rtype: str
    """
    text = text or f"Enter the PUK ({card.puk_rule}): "
    return _get_code(card.valid_puk, text, allowed_values)


def _get_code(
        validation_method: typing.Callable,
        text: str = "",
        allowed_values: List = None) -> str:
    allowed_values = allowed_values or []
    code = ui.secret_with_exit(text, required=("" not in allowed_values))

    if not {code, ""}.isdisjoint(allowed_values):
        return code

    while True:
        try:
            validation_method(code)
        except cryptnoxpy.exceptions.DataValidationException as error:
            print(error, "\n")
            code = ui.secret_with_exit(text, required=("" not in allowed_values))

            if code in allowed_values:
                break
        else:
            break

    return code

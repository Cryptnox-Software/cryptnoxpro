# -*- coding: utf-8 -*-
"""
Module dealing with security of the application.
"""
import typing
from typing import List, Dict

import cryptnoxpy
from stdiomask import getpass

DEMO_PIN = "000000000"


def demo_puk(card):
    return "0" * card.PUK_LENGTH


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
    demo_card = is_demo(card.info)

    while not authorized:
        if demo_card:
            print("The card is in demo mode, just press ENTER. The PIN will be from DEMO mode "
                  "regardless of what you type.")

        pin_code = get_pin_code(card, text, [""] if demo_card else [])

        if demo_card:
            pin_code = DEMO_PIN

        try:
            authorized = _check_pin_code(card, pin_code, not demo_card)
        except cryptnoxpy.PinException:
            if demo_card:
                print("Demo PIN doesn't work. Try other PIN code.\n")
                demo_card = False
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


def is_demo(card_info: Dict):
    try:
        return card_info["name"] == card_info["email"] == "DEMO"
    except TypeError:
        return False


def process_command_with_puk(card: cryptnoxpy.Card, function: typing.Callable, *args, **kwargs) -> bool:
    demo_mode = is_demo(card.info)

    while True:
        if demo_mode:
            print("The card is in demo mode, just press ENTER. The PUK will be from DEMO mode "
                  "regardless of what you type.")

        puk_code = get_puk_code(card, allowed_values=[""] if is_demo else [])
        if demo_mode:
            puk_code = demo_puk(card)

        try:
            result = function(*args, **kwargs, puk=puk_code)
        except cryptnoxpy.PukException as error:
            if demo_mode:
                print("Demo PUK doesn't work. Try other PUK code.\n")
                demo_mode = False
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
    except cryptnoxpy.PinException as error:
        if not handle_exception:
            raise error
        number_of_retries = error.number_of_retries
        if number_of_retries == 0:
            raise
        print(f"Wrong pin code. You have {number_of_retries} before the card is locked.")

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


def _get_code(validation_method: typing.Callable, text: str = "", allowed_values: List = None) -> str:
    allowed = allowed_values[:] if allowed_values else []
    code = getpass(prompt=text)

    if code in allowed:
        return code

    try:
        allowed.remove("")
    except ValueError:
        pass

    while True:
        try:
            validation_method(code)
        except cryptnoxpy.DataValidationException as error:
            print(error, "\n")
            code = getpass(prompt=text)

            if code in allowed:
                break
        else:
            break

    return code

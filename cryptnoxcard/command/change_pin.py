# -*- coding: utf-8 -*-
"""
Module containing command for changing PIN code of the card
"""
import cryptnoxpy

from .helper import security
from .command import Command

try:
    import enums
except ImportError:
    from .. import enums


class ChangePin(Command):
    """
    Command to change the PIN code of the card
    """
    _name = enums.Command.CHANGE_PIN.value

    def _execute(self, card) -> int:
        if card.auth_type != cryptnoxpy.AuthType.PIN:
            security.check_pin_code(card)

        if security.is_demo(card.info):
            print("Card is in demo mode. Setting same PIN code")
            pin_code = security.DEMO_PIN
        else:
            pin_code = security.get_pin_code(card, f"Set new PIN code ({card.pin_rule}): ")

        card.change_pin(pin_code)

        print("PIN changed successfully")

        return 0

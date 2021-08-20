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


class ChangePuk(Command):
    """
    Command to change the PIN code of the card
    """
    _name = enums.Command.CHANGE_PUK.value

    def _execute(self, card: cryptnoxpy.Card) -> int:
        demo_mode = security.is_demo(card.info)
        if demo_mode:
            print("The card is in demo mode, just press ENTER. The PUK will be from DEMO mode "
                  "regardless of what you type.")

        puk_code = security.get_puk_code(card, f"   Enter the PUK ({card.puk_rule}): ",
                                         [""] if demo_mode else [])

        if security.is_demo(card.info):
            print("Card is in demo mode. Setting same PUK code")
            new_puk_code = security.demo_puk(card)
        else:
            new_puk_code = security.get_puk_code(card, f"Set new PUK code ({card.puk_rule}): ")

        card.change_puk(puk_code, new_puk_code)

        print("PUK changed successfully")

        return 0

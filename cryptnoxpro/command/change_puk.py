# -*- coding: utf-8 -*-
"""
Module containing command for changing PIN code of the card
"""
import cryptnoxpy

from .command import Command
from .helper import (
    security,
    ui
)

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
        if not card.initialized:
            ui.print_warning("Card is not initialized")
            print("To initialize card run : init\nTo initialize card in easy mode run : init -e")

            return -1

        easy_mode = security.is_easy_mode(card.info)
        if easy_mode:
            print("The card is in easy mode, just press ENTER. The PUK will be from EASY mode "
                  "regardless of what you type.")

        puk_code = security.get_puk_code(card, f"   Enter the PUK ({card.puk_rule}): ",
                                         [""] if easy_mode else [])

        if easy_mode:
            puk_code = security.easy_mode_puk(card)

        card.change_puk(puk_code, puk_code)

        if security.is_easy_mode(card.info):
            print(f"Card is in {security.EASY_MODE_TEXT}. Setting same PUK code")
            new_puk_code = security.easy_mode_puk(card)
        else:
            new_puk_code = security.get_puk_code(card, f"Set new PUK code ({card.puk_rule}): ")

        card.change_puk(puk_code, new_puk_code)

        print("PUK changed successfully")

        return 0

# -*- coding: utf-8 -*-
"""
Module containing command for resetting content of card to factory default
"""
import cryptnoxpy

from .helper import security
from .command import Command

try:
    import enums
except ImportError:
    from .. import enums


class Reset(Command):
    """
    Command to reset the card to its factory settings.

    Warning: This command will delete the keys from the card, which may result
             in loss of access to the funds.
    """
    _name = enums.Command.RESET.value

    def _execute(self, card: cryptnoxpy.Card) -> int:
        if not card.initialized:
            print("Card is not initialized. Already cleared.")
            return 0

        serial_number = card.serial_number
        security.process_command_with_puk(card, card.reset)

        del self._cards[serial_number]
        print("Card was reset successfully.")

        return 0

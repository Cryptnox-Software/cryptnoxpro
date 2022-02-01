# -*- coding: utf-8 -*-
"""
Module containing command for initializing cards
"""
from .command import Command

from . import erc_token
from . import card as card_command

try:
    import enums
except ImportError:
    from .. import enums

class Initialize(Command):
    """
    Command to initialize the card
    """
    _name = enums.Command.INITIALIZE.value

    def _execute(self, card) -> int:
        card_types = {
            ord("N"): erc_token.Initialize,
            ord("B"): card_command.Initialize,
        }

        try:
            command = card_types[card.type](self.data, self._cards)
        except KeyError:
            print("Method not supported with this card type.")
            return -2

        return command.execute(card)

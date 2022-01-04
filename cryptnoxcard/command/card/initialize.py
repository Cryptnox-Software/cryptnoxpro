# -*- coding: utf-8 -*-
"""
Module containing command for initializing a card
"""

from tabulate import tabulate

from ..command import Command
from ..helper import ui

try:
    import enums
except ImportError:
    from ... import enums


class Initialize(Command):
    """
    Command to initialize a card with: username and email, PIN and PUK codes.
    """
    _name = enums.Command.INITIALIZE.value

    def _execute(self, card) -> int:
        if card.initialized:
            print("Card already initialized.")
            return 1

        print("Cryptnox Initialisation\n")

        init_data = ui.get_init_data(card, self.data.demo)

        print("\nInitializing the applet\n")

        card.init(init_data.name, init_data.email, init_data.pin, init_data.puk)

        print("Card has been initialized.")
        if self.data.demo:
            print("Card is in demo mode.\n\nPress enter for all pin and puk prompts.\n")

        print(tabulate([["RUN seed COMMAND TO GENERATE NEW OR LOAD AN EXISTING SEED."]],
                       tablefmt="rst"))

        del self._cards[card.serial_number]

        return 0

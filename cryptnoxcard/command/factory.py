# -*- coding: utf-8 -*-
"""
Module for creating Factory class.
"""
from argparse import Namespace

from .command import Command
from .helper.cards import Cards
from .unknown import Unknown


class Factory:
    """
    Factory class to populate the command line parser and get command that can
    work with the user input.

    :param Namespace data: Command line arguments and options
    :param Cards cards: List of cards to use for the command
    """

    def __init__(self, data: Namespace, cards: Cards = None):
        self.data = data
        self.cards = cards

    def get_command(self) -> Command:
        """
        Gives back the command that took responsibility for executing the
        command

        :return: Command that can execute the given user input
        :rtype: Command
        """
        from .btc import Btc  # pylint: disable=unused-import
        from .card_configuration import CardConfiguration  # pylint: disable=unused-import
        from .change_pin import ChangePin  # pylint: disable=unused-import
        from .change_puk import ChangePuk  # pylint: disable=unused-import
        from .config import Config  # pylint: disable=unused-import
        from .eosio import Eosio  # pylint: disable=unused-import
        from .eth import Eth  # pylint: disable=unused-import
        from .history import History  # pylint: disable=unused-import
        from .info import Info  # pylint: disable=unused-import
        from .initialize import Initialize  # pylint: disable=unused-import
        from .seed import Seed  # pylint: disable=unused-import
        from .cards import Cards  # pylint: disable=unused-import
        from .reset import Reset  # pylint: disable=unused-import
        from .unlock_pin import UnlockPin  # pylint: disable=unused-import
        from .user_key import UserKey  # pylint: disable=unused-import

        for command in Command.__subclasses__():
            try:
                if command.meets_condition(self.data):
                    return command(self.data, self.cards)
            except KeyError:
                continue

        return Unknown(self.data)

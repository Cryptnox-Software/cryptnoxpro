# -*- coding: utf-8 -*-
"""
Module for creating Factory class.
"""
from argparse import Namespace

from .command import Command
from .helper.cards import Cards
from .unknown import Unknown


def command(data: Namespace, cards: Cards = None) -> Command:
    """
    Gives back the command that took responsibility for executing the
    command

    :param Namespace data: Command line arguments and options
    :param Cards cards: List of cards to use for the command
    :param int card_type: Card type to work with

    :return: Command that can execute the given user input
    :rtype: Command
    """
    from .btc import Btc  # pylint: disable=unused-import
    from .card_configuration import CardConfiguration  # pylint: disable=unused-import
    from .change_pin import ChangePin  # pylint: disable=unused-import
    from .change_puk import ChangePuk  # pylint: disable=unused-import
    from .config import Config  # pylint: disable=unused-import
    from .eth import Eth  # pylint: disable=unused-import
    from .history import History  # pylint: disable=unused-import
    from .info import Info  # pylint: disable=unused-import
    from .initialize import Initialize  # pylint: disable=unused-import
    from .seed import Seed  # pylint: disable=unused-import
    from .cards import Cards  # pylint: disable=unused-import
    from .server import Server  # pylint: disable=unused-import
    from .reset import Reset  # pylint: disable=unused-import
    from .unlock_pin import UnlockPin  # pylint: disable=unused-import
    from .user_key import UserKey  # pylint: disable=unused-import
    from .transfer import Transfer  # pylint: disable=unused-import
    from .get_xpub import getXpub  # pylint: disable=unused-import
    from .get_clearpubkey import GetClearpubkey  # pylint: disable=unused-import
    from .decrypt import Decrypt  # pylint: disable=unused-import

    for cls in Command.__subclasses__():
        if cls.meets_condition(data):
            return cls(data, cards)

    return Unknown(data)

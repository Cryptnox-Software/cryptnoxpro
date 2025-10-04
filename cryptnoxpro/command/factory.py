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
    from .btc import Btc  # noqa: F401
    from .card_configuration import CardConfiguration  # noqa: F401
    from .change_pin import ChangePin  # noqa: F401
    from .change_puk import ChangePuk  # noqa: F401
    from .config import Config  # noqa: F401
    from .eth import Eth  # noqa: F401
    from .history import History  # noqa: F401
    from .info import Info  # noqa: F401
    from .initialize import Initialize  # noqa: F401
    from .seed import Seed  # noqa: F401
    from .cards import Cards  # noqa: F401
    from .server import Server  # noqa: F401
    from .reset import Reset  # noqa: F401
    from .unlock_pin import UnlockPin  # noqa: F401
    from .user_key import UserKey  # noqa: F401
    from .transfer import Transfer  # noqa: F401
    from .get_xpub import getXpub  # noqa: F401
    from .get_clearpubkey import GetClearpubkey  # noqa: F401
    from .decrypt import Decrypt  # noqa: F401

    for cls in Command.__subclasses__():
        if cls.meets_condition(data):
            return cls(data, cards)

    return Unknown(data)

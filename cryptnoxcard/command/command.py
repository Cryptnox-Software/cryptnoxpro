# -*- coding: utf-8 -*-
"""
Module containing abstract class for creating command child classes
"""
import abc

import cryptnoxpy
from argparse import Namespace
from tabulate import tabulate

from . import user_keys
from .helper import security
from .helper.cards import (
    Cards,
    ExitException,
    TimeoutException
)

try:
    from config import get_configuration, save_to_config
except ImportError:
    from ..config import get_configuration, save_to_config


class Command(metaclass=abc.ABCMeta):
    """
    Base class for all commands

    :param Namespace data: Command line arguments
    """

    def __init__(self, data: Namespace, cards: Cards = None):
        self.data = data
        self._cards = cards or Cards()
        self.serial_number = None
        # self.notification = Notification()

    def execute(self, serial_number: int = None) -> int:
        """
        Main execution method of the command.

        Finds card and establishes connection to it. Executes _execute method.
        :param serial_number: Serial number of the wanted card
        :return: 0 if the command executed without issues. Other number
                 indicating and issue
        :rtype: int
        """
        result = self._handle_execution(serial_number)
        # self.print_notifications()

        return result

    def _handle_execution(self, serial_number: int = None) -> int:
        self.serial_number = serial_number
        try:
            self.serial_number = self.data.serial
        except AttributeError:
            pass
        try:
            card = self._cards[self.serial_number]
        except (ExitException, TimeoutException, cryptnoxpy.CryptnoxException) as error:
            print(error)
            return -1

        self.run_execute(card)

    def print_notifications(self):
        return
        notifications = self.notification.get()
        for card_serial, contracts_events in notifications.items():
            title = "\n\nLIST OF NEW EVENTS"
            display_title = True
            tabulate_table = []
            contract_name = None
            for contract, events in contracts_events.items():
                for event, new_events_num in events.items():
                    if contract_name != contract:
                        table_contract = contract
                        contract_name = contract
                    else:
                        table_contract = ""
                    tabulate_table.append(
                        [table_contract, event, new_events_num])
            if tabulate_table and display_title:
                print(title)
            if tabulate_table:
                print(f"\nCARD: {card_serial}")
                print(tabulate(tabulate_table,
                               headers=["CONTRACT", "EVENT", "NEW EVENTS"]),
                      "\n")

    def run_execute(self, card) -> int:
        print(f"Using card with serial number {card.serial_number}")

        try:
            result = self._execute(card)
        except cryptnoxpy.InitializationException as error:
            print("\n" + tabulate([[str(error).upper()]],
                                  tablefmt="rst"))
            print("To initialize card run init."
                  "\nTo initialize in demo mode run init -d\n")
            result = -1
        except cryptnoxpy.SeedException:
            print("The seed is not generated\nRun seed command to generate seed")
            result = -1
        except (cryptnoxpy.CryptnoxException, NotImplementedError) as error:
            print(error)
            result = -1

        return result

    @property
    @abc.abstractmethod
    def _name(self):
        pass

    @abc.abstractmethod
    def _execute(self, card) -> int:
        """
        Method that will be executed in executed in execute method.

        :param connection cryptnoxpy.Connection: Connection to the card
        :return: Execution status
        """

    @classmethod
    def meets_condition(cls, data: Namespace) -> bool:
        """
        Take responsibility for command line arguments for processing.

        :param Namespace data: Command line arguments given by user

        :return: Whether this class can handle the user request
        :rtype: bool
        """
        return data.command == cls._name

    @classmethod
    def __subclasshook__(cls, c):
        if cls is Command:
            attrs = set(dir(c))

            if set(cls.__abstractmethods__) <= attrs:
                return True

        return NotImplemented

    @staticmethod
    def _check(card, check_seed: bool = True) -> bool:
        """
        Check if card is initialized and pin code is saved.

        :param Card card: Card to use
        :param bool check_seed: If True checks if seed is generated
        :return:
        """
        if card.open:
            return True

        card.check_init()

        if not card.valid_key and check_seed:
            raise cryptnoxpy.SeedException("The key is not generated")

        result = False
        try:
            result = user_keys.authenticate(card)
        except NotImplementedError:
            pass

        if not result:
            result = bool(security.check_pin_code(card))

        return result

        # get_configuration(serial_number)
        # self.notification.run()

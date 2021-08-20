# -*- coding: utf-8 -*-
"""
Module containing command for initializing a card
"""
import secrets
import sys

import cryptnoxpy
from tabulate import tabulate

from .helper import security
from .command import Command
from tabulate import tabulate

try:
    import enums
except ImportError:
    from .. import enums


class StringConvert(str):
    """
    Class for finding if string can be converted to ascii.
    """
    def isascii_(self) -> bool:
        """
        Finding if string can be converted or is ascii.

        :return: Can be or is ascii.
        """
        if sys.version_info[1] == 6:
            try:
                self.encode('ascii')
            except UnicodeEncodeError:
                return False
            else:
                return True
        else:
            return self.isascii()


class Initialize(Command):
    """
    Command to initialize a card with: user name and email, PIN and PUK codes.
    """
    _name = enums.Command.INITIALIZE.value

    def _execute(self, card) -> int:
        pairing_secret = b""

        if card.initialized:
            print("Card already initialized.")
            return 1

        print("Cryptnox Initialisation\n")
        if self.data.demo and not Initialize._confirm_demo():
            return 0
        print("You can enter exit at any point to exit initialisation process.")
        print("Setting Cryptnox parameters\n")

        if self.data.demo:
            owner_name = "DEMO"
            owner_email = "DEMO"
            puk_code = security.demo_puk(card)
            puk_choice = "1"
            pin_code = security.DEMO_PIN
            data = [
                ["Owner's name", ":", owner_name],
                ["Owner's email", ":", owner_email],
                [f"Card PUK code ({card.puk_rule})", ":", puk_code],
                [f"Card PIN code ({card.pin_rule})", ":", pin_code]
            ]
            print(tabulate(data, tablefmt="plain"))
        else:
            try:
                owner_name = Initialize._handle_exit(
                    Initialize._get_owner_name())
                owner_email = Initialize._handle_exit(
                    Initialize._get_owner_email())
                puk_code, puk_choice = self._get_puk_code(card)
                pin_code = self._get_pin_code(card)
            except KeyboardInterrupt:
                return 0

        print("\nInitializing the applet\n")

        card.init(owner_name, owner_email, pin_code, puk_code, pairing_secret)

        if puk_choice == "2":
            print("-- Card PUK code : ", puk_code)
            print("-- Save the PUK on a paper for security  --")

        print("Card has been initialized.")
        if self.data.demo:
            print("Card is in demo mode."
                  "\n\nPress enter for all pin and puk prompts.\n")

        print(tabulate([["RUN KEY COMMAND TO GENERATE A SEED."]],
                       tablefmt="rst"))

        del self._cards[card.serial_number]

        return 0

    @staticmethod
    def _get_valid_input(text: str, valid, error: str = "Invalid value") -> str:
        user_input = StringConvert(input(text))
        while not valid(user_input):
            print(error)
            user_input = StringConvert(input(text))

        return user_input

    @staticmethod
    def _verify_input(card: cryptnoxpy.Card, method, text, verify_text,
                      error: str = "The given values are not the same.") -> str:
        while True:
            value = Initialize._handle_exit(
                method(card, text, allowed_values=["exit"]))
            verify_value = Initialize._handle_exit(
                method(card, verify_text, allowed_values=["exit"]))

            if value == verify_value:
                break

            print(error)

        return value

    def _get_puk_code(self, card):
        print(f"For the PUK code: 1) Input your own {card.puk_rule} PUK")
        print("                   2) Generate a random one ")
        puk_choice = Initialize._handle_exit(input("> "))
        while puk_choice not in ["1", "2"]:
            print("Not a valid choice. Please, enter 1 or 2.")
            puk_choice = input("> ")

        if puk_choice == "2":
            puk_code = str(secrets.randbelow(10 ** card.PUK_LENGTH)).zfill(card.PUK_LENGTH)
        else:
            puk_code = self._verify_input(card, security.get_puk_code,
                                          f" Set card PUK code ({card.puk_rule}): ",
                                          f"   Repeat PUK code ({card.puk_rule}): ")

        return puk_code, puk_choice

    def _get_pin_code(self, card):
        return self._verify_input(card, security.get_pin_code,
                                  f"Set card PIN code ({card.pin_rule}): ",
                                  f"  Repeat PIN code ({card.pin_rule}): ")

    @staticmethod
    def _get_owner_name() -> str:

        return Initialize._get_valid_input("Owner's name:",
                                           lambda text: text.isascii_() and len(text) <= 20,
                                           "ERROR when input owner name, should be ASCII string no "
                                           "longer than 20 chars.")

    @staticmethod
    def _get_owner_email() -> str:
        return Initialize._get_valid_input("Owner's email: ",
                                           lambda value: value.isascii_() and len(value) <= 60,
                                           "ERROR when input owner email, should be ASCII string "
                                           "no longer than 60 chars.")

    @staticmethod
    def _confirm_demo() -> bool:
        print(tabulate([["WARNING: THIS WILL INITIALIZE THE CARD IN DEMO MODE"]], tablefmt="rst"))

        while True:
            conf = input("\nDo you wish to proceed ? [y/N] > ")
            if conf.lower() in ("y", "n", ""):
                break
            print('Type "y", "n" or leave empty for no.')

        return conf.lower() == "y"

    @staticmethod
    def _handle_exit(value):
        if value == "exit":
            raise KeyboardInterrupt
        return value

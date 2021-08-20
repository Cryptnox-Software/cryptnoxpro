# -*- coding: utf-8 -*-
"""
Module containing command for generating keys on the card
"""

import cryptnoxpy

from . import user_keys
from .command import Command
from .helper import security
from .helper.cards import ExitException, TimeoutException

try:
    import enums
    from lib import cryptos
except ImportError:
    from .. import enums
    from ..lib import cryptos


class Seed(Command):
    """
    Command to generate keys on the card
    """
    _name = enums.Command.SEED.value

    def _execute(self, card) -> int:
        result = 0

        card.check_init()

        if card.valid_key:
            print("\nKey is already generated"
                  "\nReset the card before generating another one")
            return 0

        if self.data.method == "upload":
            Seed._upload(card)
        elif self.data.method == "chip":
            Seed._chip(card)
        elif self.data.method == "recover":
            Seed._recover(card)
        elif self.data.method == "dual":
            result = self._dual_seed(card)
        else:
            print("Method not valid.")
            result = 1

        return result

    @staticmethod
    def _chip(card) -> None:
        pin_code = Seed._get_pin_code(card)

        card.generate_seed(pin_code)
        print("New key generated in card.")

    def _dual_seed(self, card) -> int:
        try:
            card.dual_seed_public_key()
        except NotImplementedError as error:
            print(error)
            return -1
        except cryptnoxpy.DataValidationException:
            pass

        pin_code = Seed._get_pin_code(card)

        serial_number = card.serial_number
        index = card.connection.index
        first_card_data = card.dual_seed_public_key(pin_code)

        print(f"Remove card with serial number {serial_number} (first card) and insert the second "
              f"card into same reader with index {index}.")
        input("Insert card and press ENTER to continue")

        second_card = self._get_second_card(index, serial_number)

        pin_code = Seed._get_pin_code(second_card)
        second_card_data = second_card.dual_seed_public_key(pin_code)
        second_card.dual_seed_load(first_card_data, pin_code)
        print(f"Remove card with serial number {second_card.serial_number} (second card) and "
              f"insert the card with serial number {serial_number} (first card) into the same "
              f"reader with index {index}.")
        input("Insert card and press ENTER to continue")
        del self._cards[card.serial_number]

        try:
            card = self._cards[serial_number]
        except (ExitException, TimeoutException) as error:
            print(error)
            print("First card seed has been generated. Reset it before doing dual seed generation "
                  "again.")
            return -2

        pin_code = Seed._get_pin_code(card)
        card.dual_seed_load(second_card_data, pin_code)
        print("Dual seed generation has been finished. Check with command `info` that both of them"
              "have the same addresses.")

        return 0

    @staticmethod
    def _load_mnemonic(card: cryptnoxpy.Card, mnemonic: str, pin_code: str) -> None:
        bip32_master_seed = cryptos.cryptnox_mnemonic_to_seed(mnemonic)
        card.load_seed(bip32_master_seed, pin_code)

    @staticmethod
    def _recover(card: cryptnoxpy.Card) -> None:
        pin_code = Seed._get_pin_code(card)

        print("\nEnter the mnemonic root to recover :")
        mnemonic = input("> ")
        Seed._load_mnemonic(card, mnemonic, pin_code)
        print("Mnemonic loaded, please keep it safe for backup.")

    @staticmethod
    def _upload(card: cryptnoxpy.Card) -> None:
        pin_code = Seed._get_pin_code(card)
        mnemonic = cryptos.entropy_to_words(card.generate_random_number(32))
        print("\nMnemonic root :")
        print(mnemonic)
        Seed._load_mnemonic(card, mnemonic, pin_code)
        print("\nMnemonic loaded, please save this root mnemonic for backup.")

    @staticmethod
    def _get_pin_code(card: cryptnoxpy.Card) -> str:
        card.check_init()

        pin_code = ""
        if not card.open:
            try:
                if not user_keys.authenticate(card):
                    pin_code = security.check_pin_code(card)
            except NotImplementedError:
                pin_code = security.check_pin_code(card)
        elif card.auth_type == cryptnoxpy.AuthType.PIN:
            pin_code = security.check_pin_code(card)

        return pin_code

    def _get_second_card(self, index: int, first_card_serial_number: int) -> cryptnoxpy.Card:
        while True:
            card = self._cards[index]
            if not card.initialized:
                print(f"This card, serial number {card.serial_number} is not "
                      f"initialized. Insert another card.")
                input("Press ENTER to continue.")
            if card.serial_number == first_card_serial_number:
                print(f"Please replace card with another one. First card with serial number "
                      f"{first_card_serial_number} detected.")
                input("Press ENTER to continue.")
            elif card.valid_key:
                print("\nThis card already has a seed. Insert another card or reset this one.")
                input("Press ENTER to continue.")
            else:
                try:
                    card.dual_seed_public_key()
                except NotImplementedError:
                    print(f"Second card, {card.serial_number} doesn't have this functionality. Insert "
                          f"another card")
                    input("Press ENTER to continue.")
                except cryptnoxpy.DataValidationException:
                    break
                else:
                    break

        return card

# -*- coding: utf-8 -*-
"""
Module containing command for generating keys on the card
"""
from pathlib import Path
from typing import Union

import cryptnoxpy
from tabulate import tabulate

from . import user_keys
from .command import Command
from .helper import backup, helper_methods, security
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

        if self.data.action == "backup":
            Seed._backup(card)
        elif self.data.action == "chip":
            Seed._chip(card)
        elif self.data.action == "dual":
            result = self._dual_seed(card)
        elif self.data.action == "recover":
            Seed._recover(card)
        elif self.data.action == "restore":
            Seed._restore(card)
        elif self.data.action == "upload":
            Seed._upload(card)
        else:
            print("Method not valid.")
            result = 1

        return result

    @staticmethod
    def _backup(card: cryptnoxpy.Card) -> int:
        pin_code = Seed._get_pin_code(card)

        service = Seed._backup_service()
        if not service:
            return False

        name = helper_methods.input_with_exit("Name of the seed on the KMS in HSM: ")

        seed = card.generate_random_number(32)
        print("Backing up seed...")
        try:
            service.backup(name, seed)
        except backup.ExistsException:
            print(f"The backup operation failed because seed under the name {name} already exists.")
            return -1
        except backup.BackupException as error:
            print(error)
            return -1

        print("Retrieving seed from service for check...")
        try:
            decoded = service.retrieve(name)
        except backup.BackupException as error:
            print(error)
            return -1

        if decoded != seed:
            print("Retrieved and backed up data is not the same.")
            return -1

        print("Seed successfully saved. Writing card.")
        mnemonic = cryptos.entropy_to_words(seed)
        Seed._load_mnemonic(card, mnemonic, pin_code)

        data = list(service.region.items())
        data.append(("name", name))
        print("\nBackup data:\n" + tabulate(data))

        backup_file = Path.home().joinpath(f"{name}.txt")
        backup_file.write_text(tabulate(data))
        print(f"\nBackup data also saved to: {backup_file}")

        helper_methods.print_warning("It is advised to delete your AWS access keys if you "
                                     "don't plan to use them.")

        return 0

    @staticmethod
    def _backup_service() -> Union[None, backup.AWS]:
        access_key_id = helper_methods.input_with_exit("Access Key ID: ")
        secret_access_key = helper_methods.secret_with_exit("Secret Access Key: ")

        try:
            service = backup.AWS(access_key_id, secret_access_key)
        except backup.ConnectionException as error:
            print(f"Error in connecting to service: {error}")
            return None

        regions = {}
        for client, options in service.regions.items():
            for option in regions.values():
                options.remove(option)
            regions[client] = helper_methods.option_input(options)

        try:
            service.region = regions
        except ValueError:
            print("Issue with setting regions")
            return None

        return service

    @staticmethod
    def _chip(card: cryptnoxpy.Card) -> None:
        pin_code = Seed._get_pin_code(card)

        card.generate_seed(pin_code)
        print("New key generated in card.")

    def _dual_seed(self, card: cryptnoxpy.Card) -> int:
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
                    print(f"Second card, {card.serial_number} doesn't have this functionality. "
                          f"Insert another card")
                    input("Press ENTER to continue.")
                except cryptnoxpy.DataValidationException:
                    break
                else:
                    break

        return card

    @staticmethod
    def _load_mnemonic(card: cryptnoxpy.Card, mnemonic: str, pin_code: str) -> None:
        seed = cryptos.cryptnox_mnemonic_to_seed(mnemonic)
        card.load_seed(seed, pin_code)

    @staticmethod
    def _recover(card: cryptnoxpy.Card) -> None:
        pin_code = Seed._get_pin_code(card)

        print("\nEnter the mnemonic root to recover :")
        mnemonic = input("> ")
        Seed._load_mnemonic(card, mnemonic, pin_code)
        print("Mnemonic loaded, please keep it safe for backup.")

    @staticmethod
    def _restore(card: cryptnoxpy.Card) -> int:
        pin_code = Seed._get_pin_code(card)
        service = Seed._backup_service()
        if not service:
            return -1
        name = helper_methods.input_with_exit("Name of the seed on the KMS in HSM: ")

        print("Retrieving seed from service...")
        try:
            seed = service.retrieve(name)
        except backup.NotFoundException:
            print(f"Backup with name {name} not found.")
            return -1
        except backup.BackupException as error:
            print(error)
            return -1

        try:
            mnemonic = cryptos.entropy_to_words(seed)
        except ValueError:
            print("There was an issue with the retrieved backup in converting it to a mnemonic.")
            return -1

        print("Seed successfully retrieved. Writing card.")
        Seed._load_mnemonic(card, mnemonic, pin_code)
        print("\nMnemonic loaded from backup service.")

        helper_methods.print_warning("It is advised to delete your AWS access keys if you "
                                     "don't plan to use them.")

        return 0

    @staticmethod
    def _upload(card: cryptnoxpy.Card) -> None:
        pin_code = Seed._get_pin_code(card)
        seed = card.generate_random_number(32)
        mnemonic = cryptos.entropy_to_words(seed)
        Seed._load_mnemonic(card, mnemonic, pin_code)
        print("\nMnemonic root :")
        print(mnemonic)

        print("\nMnemonic loaded, please save this root mnemonic for backup.")

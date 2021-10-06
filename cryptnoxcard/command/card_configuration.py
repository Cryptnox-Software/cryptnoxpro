"""
Module containing the class for printing card configuration
"""
import cryptnoxpy
from tabulate import tabulate

from .command import Command
from .helper import security

try:
    import enums
except ImportError:
    from .. import enums


class CardConfiguration(Command):
    """
    Command for printing card configuraton
    """
    _SEED_SOURCE_TO_STRING = {
        cryptnoxpy.SeedSource.NO_SEED: "No seed",
        cryptnoxpy.SeedSource.SINGLE: "Single 256K1 EC pair",
        cryptnoxpy.SeedSource.EXTENDED: "Extended 256K1 EC pair BIP32 node",
        cryptnoxpy.SeedSource.EXTERNAL: "Externally generated",
        cryptnoxpy.SeedSource.INTERNAL: "Internally generated",
        cryptnoxpy.SeedSource.DUAL: "Dual initialized"
    }
    _name = enums.Command.CARD_CONFIGURATION.value

    def _execute(self, card: cryptnoxpy.Card) -> int:
        if self.data.value:
            if self.data.key == "pinless":
                path = "m/43'/60'/1581'" if CardConfiguration._str_to_bool(self.data.value) else ""
                security.process_command_with_puk(card, card.set_pinless_path, path=path)
                param = "PIN-less path"
            else:
                security.process_command_with_puk(card, card.set_pin_authentication,
                                                  CardConfiguration._str_to_bool(self.data.value))
                param = "PIN code authentication"
            print(f"Value for {param} changed to {self.data.value}")
            return 0

        if self.data.key:
            print("To change value use argument yes/no")
            if self.data.key == "pinless":
                print(f"PIN-less path {CardConfiguration._bool_to_str(card.pinless_enabled)}")
            else:
                print(f"PIN code authentication "
                      f"{CardConfiguration._bool_to_str(card.pin_authentication)}")
            return 0

        return CardConfiguration.show(card)

    @staticmethod
    def show(card: cryptnoxpy.Card) -> int:
        data = [
            ["Card initialisation", CardConfiguration._bool_to_str(card.initialized)]
        ]
        try:
            data += [["Seed source", CardConfiguration._SEED_SOURCE_TO_STRING[card.seed_source]]]
        except NotImplementedError:
            data += [["Seed source", CardConfiguration._bool_to_str(card.valid_key)]]

        data += [
            ["PIN code authentication", CardConfiguration._bool_to_str(card.pin_authentication)],
            ["PIN-less path", CardConfiguration._bool_to_str(card.pinless_enabled)],
            ["Extended public key", CardConfiguration._bool_to_str(card.extended_public_key)],
        ]
        try:
            data += [
                ["RSA 2048 user key", CardConfiguration._bool_to_str(card.user_key_enabled(cryptnoxpy.SlotIndex.RSA))],
                ["ECC 256 user key",
                 CardConfiguration._bool_to_str(card.user_key_enabled(cryptnoxpy.SlotIndex.EC256R1))],
                ["FIDO2 user key", CardConfiguration._bool_to_str(card.user_key_enabled(cryptnoxpy.SlotIndex.FIDO))]
            ]
        except NotImplementedError:
            data += [["User keys", "Not available"]]

        print(tabulate(data, tablefmt="plain"))

        return 0

    @staticmethod
    def _bool_to_str(value: bool) -> str:
        return "yes" if value else "no"

    @staticmethod
    def _str_to_bool(value: str) -> bool:
        return value == "yes"

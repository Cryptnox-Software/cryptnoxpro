"""
Module containing the class for printing card configuration
"""
import cryptnoxpy
from tabulate import tabulate

from .command import Command

try:
    import enums
except ImportError:
    from .. import enums


class CardConfiguration(Command):
    """
    Command for printing card configuraton
    """
    _SEED_SOURCE_TO_STRING = {
        cryptnoxpy.SeedSource.NO_SEED: "no seed",
        cryptnoxpy.SeedSource.SINGLE: "Single 256K1 EC pair",
        cryptnoxpy.SeedSource.EXTENDED: "Extended 256K1 EC pair BIP32 node",
        cryptnoxpy.SeedSource.EXTERNAL: "Externally generated",
        cryptnoxpy.SeedSource.INTERNAL: "Internally generated",
        cryptnoxpy.SeedSource.DUAL: "Dual initialized"
    }
    _name = enums.Command.CARD_CONFIGURATION.value

    @staticmethod
    def _bool_to_str(value: bool) -> str:
        return "yes" if value else "no"

    def _execute(self, card) -> int:
        data = [
            ["Card initialisation", CardConfiguration._bool_to_str(card.initialized)],
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
                ["ECC 256 user key", CardConfiguration._bool_to_str(card.user_key_enabled(cryptnoxpy.SlotIndex.EC256R1))],
                ["FIDO2 user key", CardConfiguration._bool_to_str(card.user_key_enabled(cryptnoxpy.SlotIndex.FIDO))]
            ]
        except NotImplementedError:
            data += [["User keys", "Not available"]]

        print(tabulate(data, tablefmt="plain"))

        return 0

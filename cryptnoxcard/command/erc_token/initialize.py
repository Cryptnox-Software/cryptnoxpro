import gzip
import json
from typing import List

import cryptnoxpy

from ..command import Command
from ..helper import ui
from ..helper.cards import ExitException

try:
    import enums
    from wallet import eth
except ImportError:
    from ... import enums
    from ...wallet import eth


class Initialize(Command):
    _name = enums.Command.INITIALIZE.value

    def _execute(self, card: cryptnoxpy.Card) -> int:
        if card.initialized:
            print("Card already initialized.")
            return 1

        print("Cryptnox Initialisation\n")

        init_data = ui.get_init_data(card, self.data.demo)
        nfc_sign = ui.confirm("Sign with NFC:")

        print("Select type of token to initialize the card with:")
        try:
            token_type = ui.option_input({"nft": "NFT (ERC721)", "token": "Token (ERC20)"}, "Token Type")
        except ExitException as error:
            print(error)
            return -1

        print(token_type)
        if token_type == "nft":
            slots = Initialize._nft_slots()
        elif token_type == "token":
            slots = Initialize._token_slots()
        else:
            return -1

        self._init_card(card, init_data, nfc_sign, slots)

        serial_number = card.serial_number
        del self._cards[serial_number]
        card = self._cards[serial_number]

        if ui.confirm("Configure another card with same information?"):
            self._dual_seed(card, init_data, nfc_sign, slots)
        else:
            Initialize._seed(card, init_data.pin)

            print("Cards have been initialized.")
            if self.data.demo:
                print("Cards are in demo mode.\n\nPress enter for all pin and puk prompts.\n")

        return 0

    def _dual_seed(self, card: cryptnoxpy.Card, init_data, nfc_sign, slots: List[str]):
        serial_number = card.serial_number
        card.verify_pin(init_data.pin)
        first_pair = card.dual_seed_public_key(init_data.pin)
        index = card.connection.index
        del self._cards[index]
        input("Please, insert card pair that will be used for dual initialization and press ENTER.")
        dual_card = self._cards[index]
        while True:
            if not isinstance(dual_card, cryptnoxpy.card.Nft):
                print("This card is not an NFT card")
            elif dual_card.serial_number == serial_number:
                print("This is the same card as the first check was done on.")
            elif dual_card.initialized:
                print("This card is already initialized.")
            elif dual_card.seed_source != cryptnoxpy.SeedSource.NO_SEED:
                print("This card has a seed.")
            else:
                break
            del self._cards[index]
            input("Please, insert card pair that will be used for dual initialization and press ENTER.")
            dual_card = self._cards[index]

        self._init_card(dual_card, init_data, nfc_sign, slots)
        second_serial_number = dual_card.serial_number
        del self._cards[second_serial_number]
        dual_card = self._cards[second_serial_number]
        dual_card.verify_pin(init_data.pin)
        second_pair = dual_card.dual_seed_public_key(init_data.pin)
        dual_card.dual_seed_load(first_pair, init_data.pin)
        del self._cards[index]
        input(f"Please, insert card with serial number {serial_number} and press ENTER.")
        card = self._cards[serial_number]
        card.verify_pin(init_data.pin)
        card.dual_seed_load(second_pair, init_data.pin)

        print("Card has been initialized.")
        if self.data.demo:
            print("Card is in demo mode.\n\nPress enter for all pin and puk prompts.\n")

    def _init_card(self, card: cryptnoxpy.Card, init_data: ui.InitData, nfc_sign: bool,
                   slots: List[str]):
        print("\nInitializing the applet\n")
        card.init(init_data.name, init_data.email, init_data.pin, init_data.puk, nfc_sign=nfc_sign)
        serial_number = card.serial_number

        del self._cards[serial_number]
        card = self._cards[serial_number]
        card.verify_pin(init_data.pin)

        print("Writing data...")
        for index, value in enumerate(slots):
            if value:
                card.user_data[index] = gzip.compress(value.encode("UTF8"))
        print("Data written")

    @staticmethod
    def _nft_slots() -> List[str]:
        print("-------------------------------------------------")
        print("\n\nNFT data")
        print("-------------------------------------------------")
        endpoint = ui.input_with_exit("Endpoint URL: ").lower()
        chain_id = ui.input_type("Chain ID: ", type_of_input=int)
        contract_address = ui.input_with_exit("Contract address: ")
        nft_id = ui.input_with_exit("NFT ID: ")
        return [
            json.dumps({
                "endpoint": endpoint,
                "chain_id": chain_id,
                "contract_address": contract_address,
                "nft_id": nft_id,
            }),
            ui.input_with_exit("ABI: "),
            ui.input_with_exit("Metadata: ")
        ]

    @staticmethod
    def _seed(card: cryptnoxpy.Card, pin_code: str) -> None:
        print("Generating seed...")
        card.generate_seed(pin_code)
        print("Seed generated")
        public_key = card.get_public_key()
        address = eth.checksum_address(public_key)
        ui.print_warning(f"Your address is: {address}"
                         f"\nTransfer tokens to it to complete the initialization process.")

    @staticmethod
    def _token_slots():
        print("-------------------------------------------------")
        print("\n\nToken data")
        print("-------------------------------------------------")
        endpoint = ui.input_with_exit("Endpoint URL: ").lower()
        chain_id = ui.input_type("Chain ID: ", type_of_input=int)
        contract_address = ui.input_with_exit("Contract address: ")

        return [
            json.dumps({
                "erc": 20,
                "endpoint": endpoint,
                "chain_id": chain_id,
                "contract_address": contract_address,
            })
        ]

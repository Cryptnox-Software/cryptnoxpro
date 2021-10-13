# -*- coding: utf-8 -*-
"""
Module containing command for sending funds
"""
from typing import List

import cryptnoxpy

from .command import Command
from .helper.config import create_config_method
from .helper.helper_methods import sign
from .helper.security import check_pin_code

try:
    import enums
    from config import get_configuration
    from wallet.btc import BTCwallet, BlkHubApi
except ImportError:
    from .. import enums
    from ..config import get_configuration
    from ..wallet.btc import BTCwallet, BlkHubApi


class Btc(Command):
    """
    Command for sending payment on Bitcoin and Ethereum networks
    """
    PATH = "m/44'/0'/0'/0"

    _name = enums.Command.BTC.value

    def _execute(self, card) -> int:
        self._check(card)

        if self.data.action == "send":
            self._send(card)
        if self.data.action == "config":
            return create_config_method(card, self.data.key, self.data.value, "btc")

        return 0

    def _send(self, card: cryptnoxpy.Card) -> None:
        config = get_configuration(card)["btc"]
        network = self.data.network or config.get("network", "testnet")
        fees = self.data.fees or int(config.get("fees", 2000))

        try:
            derivation = cryptnoxpy.Derivation[config["derivation"]]
        except KeyError:
            print("Derivation is invalid")
            return

        endpoint = BlkHubApi(network)

        pubkey = card.get_public_key(derivation, path=Btc.PATH)
        wallet = BTCwallet(pubkey, network, endpoint, card)
        print("Sending BTC")
        amount = int(self.data.amount * 10 ** 8)
        # btc path in the current key
        card.derive(path=Btc.PATH)

        try:
            wallet.prepare(self.data.address, amount, fees)

            signatures = Btc._sign(card, derivation, wallet.data_hash)
            message = wallet.send(self.data.address, amount, signatures)
        except Exception as error:
            print(error)
            return

        if message.startswith("\nDONE"):
            print(f"\nTransaction id: {message[13:]}\nBalance might take 30 s to be refreshed")

    @staticmethod
    def _sign(card: cryptnoxpy.Card, derivation: cryptnoxpy.Derivation,
              data_hashes: List[bytes]) -> List[bytes]:
        signatures = []
        pin_code = check_pin_code(card) if len(data_hashes) > 1 else None

        for data_hash in data_hashes:
            signature = sign(card, data_hash, derivation, path=Btc.PATH, pin_code=pin_code)
            signatures.append(signature)

        return signatures

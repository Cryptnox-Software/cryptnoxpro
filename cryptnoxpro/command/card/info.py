# -*- coding: utf-8 -*-
from typing import List, Dict

import cryptnoxpy
import web3
from argparse import Namespace
from tabulate import tabulate

from ..cards import Cards
from ..helper.security import (
    check,
    is_easy_mode
)

try:
    import enums
    from config import get_configuration
    from wallet import eth
    from wallet.btc import BTCwallet, BlkHubApi
except ImportError:
    from ... import enums
    from ...config import get_configuration
    from ...wallet import eth
    from ...wallet.btc import BTCwallet, BlkHubApi


class Info:
    def __init__(self, data: Namespace, cards: Cards = None):
        self.data = data
        self._cards = cards or Cards(self.data.verbose if "verbose" in self.data else False)
        self.serial_number = None

    @staticmethod
    def execute(card) -> int:
        check(card)

        print("Gathering information from the network...")
        eth_info = Info._get_eth_info(card)

        Info._print_info_table([Info._get_btc_info(card), eth_info])

        config = get_configuration(card)
        if not config["eth"]["api_key"]:
            print("\nTo use the Ethereum network. Go to https://infura.io. Register and get an "
                  "API key. Set the API key with: eth config api_key")
        if is_easy_mode(card.info) and eth_info["balance"] == "0.0 ETH":
            print(f"\nTo get some Ethereum do: wget --no-check-certificate "
                  f"https://faucet.ropsten.be/donate/{eth_info['address']}")

        return 0

    @staticmethod
    def _get_btc_info(card) -> dict:
        config = get_configuration(card)["btc"]
        try:
            derivation = cryptnoxpy.Derivation[config["derivation"]].value
        except KeyError:
            return {"name": "Bad derivation type"}
        network = config.get("network", "testnet").lower()
        endpoint = BlkHubApi(network)

        path = b"" if derivation == cryptnoxpy.Derivation.CURRENT_KEY else BTCwallet.PATH
        pubkey = card.get_public_key(derivation, path=path)

        wallet = BTCwallet(pubkey, network, endpoint, card)

        tabulate_data = {
            "name": "BTC",
            "address": wallet.address,
            "network": f"{network}"
                       f"\n   -{wallet.api.url.replace('https://', '')}"
        }

        try:
            tabulate_data["balance"] = f"{wallet.get_balance() / 10.0 ** 8} BTC"
        except Exception as error:
            print(f"There's an issue in retrieving BTC data: {error}")
            tabulate_data["balance"] = "Network issue"

        return tabulate_data

    @staticmethod
    def _get_eth_info(card) -> dict:
        config = get_configuration(card)["eth"]
        network = enums.EthNetwork[config.get("network", "ropsten").upper()]
        try:
            derivation = cryptnoxpy.Derivation[config["derivation"]].value
        except KeyError:
            return {"name": "Bad derivation type"}
        try:
            api = eth.Api(config["endpoint"], network, config["api_key"])
        except ValueError as error:
            print(error)
            return {}

        path = "" if derivation == cryptnoxpy.Derivation.CURRENT_KEY else eth.Api.PATH
        public_key = card.get_public_key(derivation, path=path, compressed=False)
        address = eth.checksum_address(public_key)

        tabulate_data = {
            "name": "ETH",
            "address": address,
            "network": f"{network.name.lower()}\n   -{api.endpoint.domain}"
        }

        try:
            tabulate_data["balance"] = f"{web3.Web3.from_wei(api.get_balance(address), 'ether')} ETH"
        except Exception as error:
            print(f"There's an issue in retrieving ETH data: {error}")
            tabulate_data["balance"] = "Network issue"

        return tabulate_data

    @staticmethod
    def _print_info_table(info: List[Dict]) -> None:
        print("\n")

        to_print = {
            "name": "No name",
            "network": "No network",
            "address": "No address",
            "balance": "--",
        }

        tabulate_header = (
            "SERVICE",
            "NETWORK",
            "ACCOUNT",
            "BALANCE",
        )

        tabulate_table = []

        for element in info:
            row = [element.get(key, val) for key, val in to_print.items()]
            tabulate_table.append(row)

        print(tabulate(tabulate_table, headers=tabulate_header,
                       colalign=("left", "left", "left", "right")))

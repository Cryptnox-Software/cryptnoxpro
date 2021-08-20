# -*- coding: utf-8 -*-
"""
Module containing command for showing information about accounts connected to
the card
"""
from typing import List, Dict

import cryptnoxpy
from tabulate import tabulate

from .command import Command
from .helper.security import is_demo
from .helper.helper_methods import printable_flags

try:
    import enums
    from config import get_configuration
    from wallet.eth import (
        checksum_address,
        Web3Api
    )
    from wallet.btc import BTCwallet, BlkHubApi
    from wallet.eos import EOSWallet
except ImportError:
    from .. import enums
    from ..config import get_configuration
    from ..wallet.eth import (
        checksum_address,
        Web3Api
    )
    from ..wallet.btc import BTCwallet, BlkHubApi
    from ..wallet.eos import EOSWallet


class Info(Command):
    """
    Command to show information about accounts connected to the card
    """
    _name = enums.Command.INFO.value

    def _execute(self, card) -> int:
        self._check(card)

        print("Gathering information from the network...")
        eosio_info = Info._get_eosio_info(card)
        eosio_info["address"] = "".join(map(lambda x: f'Account: {x}\n', eosio_info["account"])) \
                                + eosio_info.get('address', 'No address')
        eosio_info["balance"] = "".join(map(lambda x: f'{x}\n', eosio_info["balance"]))
        eth_info = Info._get_eth_info(card)
        info = [Info._get_btc_info(card), eth_info, eosio_info]

        Info._print_info_table(info)

        config = get_configuration(card.serial_number)
        if not config["eth"]["api_key"]:
            print("\nTo use the Ethereum network. Go to https://infura.io. Register and get an "
                  "API key. Set the API key with: eth config api_key")
        if is_demo(card.info):
            print(f"\nTo get some Ethereum do: wget --no-check-certificate "
                  f"https://faucet.ropsten.be/donate/{eth_info['address']}")

        return 0

    @staticmethod
    def _get_eosio_info(card) -> dict:
        path = "m/44'/194'/0'/0"
        config = get_configuration(card.serial_number)["eosio"]
        tabulate_data = {
            "name": "EOS",
            "address": "Unknown address",
            "network": "Skip EOS as endpoint is not set in the configuration",
            "balance": "--"
        }

        try:
            endpoint = config["endpoint"]
        except KeyError:
            return tabulate_data

        tabulate_data["network"] = endpoint.replace("https://", "")

        coin_symbol = config.get("coin_symbol", "EOS")
        try:
            key_type = cryptnoxpy.KeyType[config.get("key_type", "K1")]
            derivation = cryptnoxpy.Derivation[config["derivation"]].value
        except KeyError:
            return tabulate_data

        pubkey = card.get_public_key(derivation, key_type, path)
        wallet = EOSWallet(pubkey, endpoint, coin_symbol, key_type=key_type.name)

        tabulate_data["address"] = wallet.address

        try:
            tabulate_data["account"] = []
            tabulate_data["balance"] = []
            accounts = wallet.get_account()
            for index in range(len(accounts)):
                tabulate_data["account"].append(accounts[index])
                tabulate_data["balance"].append(wallet.get_balance(index))
        except IndexError:
            tabulate_data["account"].append(
                "No EOS account registered for this public key.")
            tabulate_data["balance"].append("--")
        except Exception:
            tabulate_data["address"] = "Network issue"
            tabulate_data["balance"].append("--")

        return tabulate_data

    @staticmethod
    def _get_btc_info(card) -> dict:
        path = "m/44'/0'/0'/0"
        config = get_configuration(card.serial_number)["btc"]
        try:
            derivation = cryptnoxpy.Derivation[config["derivation"]].value
        except KeyError:
            return {"name": "Bad derivation type"}
        network = config.get("network", "testnet").lower()
        endpoint = BlkHubApi(network)

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
        except Exception:
            tabulate_data["balance"] = "--"

        return tabulate_data

    @staticmethod
    def _get_eth_info(card) -> dict:
        path = "m/44'/60'/0'/0"
        config = get_configuration(card.serial_number)["eth"]
        network = config.get("network", "ropsten")
        try:
            derivation = cryptnoxpy.Derivation[config["derivation"]].value
        except KeyError:
            return {"name": "Bad derivation type"}
        api_key = config.get("api_key", "")
        endpoint = Web3Api(card, network, api_key)

        public_key = card.get_public_key(derivation, path=path, compressed=False)
        address = checksum_address(public_key)

        tabulate_data = {
            "name": "ETH",
            "address": address,
            "network": f"{network.lower()}"
                       f"\n   -{endpoint.get_domain()}"
        }

        try:
            balance = endpoint.get_balance(address) / 10.0 ** 18
        except Exception:
            tabulate_data["balance"] = "--"
        else:
            tabulate_data["balance"] = f"{balance} ETH"

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

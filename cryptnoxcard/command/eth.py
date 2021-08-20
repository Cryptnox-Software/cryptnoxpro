# -*- coding: utf-8 -*-
"""
Module containing command for sending funds
"""
import json
import re
import shutil
from pathlib import Path
from typing import Dict, Any, List

import cryptnoxpy
import requests
import web3
from argparse import Namespace
from tabulate import tabulate

from .command import Command
from .helper.config import create_config_method
from .helper.helper_methods import sign
from .helper.notification import MORE_THAN_X_RESULTS, MONTH_PERIOD_IN_BLOCKS

try:
    import enums
    from config import get_configuration, save_to_config
    from wallet import eth as wallet
    from lib import cryptos
except ImportError:
    from .. import enums
    from ..config import get_configuration, save_to_config
    from ..wallet import eth as wallet
    from ..lib import cryptos

BLOCK_OFFSET = 500
LARGE_SCREEN_SIZE = (4 - 1) * 3 + 4 + (64 + 2) + (42 + 2 + 6) + 8
ERC_PATH = Path(__file__).parent.parent.joinpath("contract_abi")


class ApiKeyException(Exception):
    """
    API key is empty
    """

def _erc_abi_file(value):
    return ERC_PATH.joinpath(f"erc{value}.json").absolute()


def _abi(config) -> Dict[str, Any]:
    try:
        path = _erc_abi_file(int(config))
    except TypeError:
        return config

    try:
        abi = json.loads(path.read_text())
    except (FileNotFoundError, PermissionError,
            json.decoder.JSONDecodeError):
        raise ValueError("ERC not recognized by the application.")

    return abi


def _large_screen():
    return shutil.get_terminal_size((80, 20)).columns > LARGE_SCREEN_SIZE


def _get_processed_json_argument(data: str) -> str:
    result = data
    if isinstance(result, list):
        result = " ".join(result)
    result = result.strip("'")
    result = re.sub(r"(\w+):", r'"\1":', result)
    result = re.sub(r"(:\s)((?!false|true)\d*\.?\d*_?\s?[a-zA-Z\.]+\d*)([,\s\}])",
                    r'\1"\2"\3', result)
    result = re.sub(r'(:.?)(")([,\s])', r'\1\2"\3', result)
    result = re.sub(r'(:\s?)([,\}\]])', r'\1""\2', result)

    return result


class Event:
    def __init__(self, data: Namespace, card):
        self.data = data
        self.card = card
        self.config = get_configuration(card.serial_number)

    def list(self) -> int:
        try:
            config = get_configuration(self.card.serial_number)[
                "hidden"]["eth"]["contract"][self.data.alias]
        except KeyError:
            print("There are no contracts with this name")
            return 1

        network = config["network"].upper()

        network = wallet.Web3Api(self.card, network, config.get("api_key"))

        try:
            abi = _abi(config["abi"])
        except ValueError as error:
            print(error)
            return 3

        w3 = network.get_web3()
        contract = w3.eth.contract(address=config["address"], abi=abi)

        tabulate_table = []
        for event in contract.abi:
            if event["type"] == "event":
                args = [[f"{arg['name']}:", arg["type"]] for arg
                        in event.get("inputs")]
                row = [event.get("name"), tabulate(args, tablefmt="plain")]
                tabulate_table.append(row)
        if tabulate_table:
            tabulate_header = ["EVENTS", "ARGUMENTS"]
            print(tabulate(tabulate_table, tabulate_header, tablefmt="grid"))
        return 0

    def logs(self):
        try:
            config = get_configuration(self.card.serial_number)[
                "hidden"]["eth"]["contract"][self.data.alias]
        except KeyError:
            print("There are no contracts with this name")
            return 1

        network = config["network"].upper()

        network = wallet.Web3Api(self.card, network, config.get("api_key", ""))

        try:
            abi = _abi(config["abi"])
        except ValueError as error:
            print(error)
            return 3

        w3 = network.get_web3()
        contract = w3.eth.contract(address=config["address"], abi=abi)

        try:
            event = getattr(contract.events, self.data.event)
        except web3.exceptions.ABIEventFunctionNotFound:
            print("The event is not defined")
            return 1

        try:
            entries = Event._get_logs(event)
        except ValueError as error:
            print(f"Error in getting the events: {error}")
            return -1
        if entries:
            tabulate_data = Event._logs_table(entries)
            header = ["", "ARGUMENTS", "TRANSACTION HASH", "BLOCK"]
            print(tabulate(tabulate_data, headers=header, tablefmt="grid"))
        else:
            print("No events have been found")
        self.config["hidden"]["eth"]["contract"][self.data.alias][self.data.event] \
            = w3.eth.block_number
        save_to_config(self.card.serial_number, self.config)

    @staticmethod
    def _get_logs(event) -> List[Dict[str, Any]]:
        min_offset = 0
        max_offset = MONTH_PERIOD_IN_BLOCKS
        offset = BLOCK_OFFSET
        current_block = event.web3.eth.block_number
        event_filter = event.createFilter(fromBlock=current_block - offset,
                                          toBlock=current_block)
        while True:
            try:
                entries = event_filter.get_all_entries()
            except ValueError as error:
                if error.args[0]["code"] != MORE_THAN_X_RESULTS:
                    raise
                max_offset = offset = ((max_offset - min_offset) // 2) + \
                                      min_offset
            else:
                if len(entries) > 25 or offset >= MONTH_PERIOD_IN_BLOCKS:
                    break
                if max_offset == MONTH_PERIOD_IN_BLOCKS:
                    min_offset = offset
                    offset *= 2
                else:
                    min_offset = offset = ((max_offset - min_offset) // 2) + \
                                          min_offset
            event_filter = event.createFilter(fromBlock=current_block - offset,
                                              toBlock=current_block)

        return list(map(dict, entries[-24::-1]))

    @staticmethod
    def _logs_table(entries):
        tabulate_table = []
        for index, entry in enumerate(entries):
            entry = dict(entry)
            args = "\n".join(f"{name}: {value}" for name, value in
                             entry["args"].items())
            transaction_hash = str(entry["transactionHash"].hex())
            if not _large_screen():
                half_hash_length = int(len(transaction_hash) / 2)
                transaction_hash = \
                    f"{transaction_hash[:half_hash_length]}\n" \
                    f"{transaction_hash[half_hash_length:]}"
            tabulate_table.append(
                [index + 1, args, transaction_hash, entry["blockNumber"]])
        return tabulate_table


class Contract(Command):
    _name = "contract"

    def _execute(self, card):
        try:
            if self.data.contract_action == "add":
                return self._add(card)
            if self.data.contract_action == "call":
                return self._call(card)
            if self.data.contract_action == "list":
                if self.data.alias and not self.data.event:
                    return self._functions(card)
                elif self.data.alias and self.data.event:
                    event = Event(self.data, card)
                    return event.list()
                else:
                    return self._list(card)
            if self.data.contract_action == "list_events":
                event = Event(self.data, card)
                return event.logs()
            if self.data.contract_action == "transact":
                return self._transact(card)
        except ApiKeyException as error:
            print(error)
            return -1

    def _get_endpoint(self, card):
        config = get_configuration(card.serial_number)
        if not config["eth"]["api_key"]:
            raise ApiKeyException("\nTo use the Ethereum network. Go to https://infura.io. "
                                  "Register and get an API key. Set the API key with: eth config "
                                  "api_key")

        try:
            network = self.data.network.upper()
        except AttributeError:
            try:
                network = config["hidden"]["eth"]["contract"][self.data.alias][
                    "network"].upper()
            except KeyError:
                network = config["eth"]["network"].upper()
        try:
            network = wallet.Network[network]
        except KeyError:
            raise LookupError("Network is invalid")

        return wallet.Web3Api(card, network, config["eth"]["api_key"])

    def _add(self, card):
        endpoint = self._get_endpoint(card)
        abi = _get_processed_json_argument(self.data.abi)

        try:
            abi_to_config = abi = json.loads(abi)
        except json.decoder.JSONDecodeError as error:
            print(f"Error in json: {error}")
            return -1

        if isinstance(abi, int):
            path = _erc_abi_file(abi)
            abi_to_config = abi
            try:
                abi = json.loads(path.read_text())
            except (FileNotFoundError, PermissionError,
                    json.JSONDecodeError):
                print("ERC not recognized by the application.")
                return -1

        w3 = endpoint.get_web3()
        try:
            w3.eth.contract(address=self.data.address, abi=abi)
        except web3.exceptions.InvalidAddress as error:
            print(error.args[0])
            return -1

        config = get_configuration(card.serial_number)
        config["hidden"]["eth"]["contract"][self.data.alias] = {
            "address": self.data.address,
            "abi": abi_to_config,
            "network": endpoint.network.name,
            "block": w3.eth.block_number
        }
        save_to_config(card.serial_number, config)
        print(f"Contract added to application. Use it with alias:"
              f" {self.data.alias}")

    def _list(self, card) -> int:
        config = get_configuration(card.serial_number)
        print("\n")

        table = []
        try:
            for alias, contract in config["hidden"]["eth"]["contract"].items():
                table.append([alias, contract['address']])
        except KeyError:
            print("There are no contracts on the card")
        else:
            if table:
                print(tabulate(table, headers=("ALIAS", "ADDRESS")))
            else:
                print("There are no contracts on the card")

        return 0

    def _functions(self, card):
        endpoint = self._get_endpoint(card)
        config = get_configuration(card.serial_number)
        try:
            config = config["hidden"]["eth"]["contract"][self.data.alias]
        except KeyError as error:
            print("Contract with alias not found")
            return 1

        tabulate_header = ("NAME", "STATE MUTABILITY", "PARAMETERS")

        tabulate_table = []

        try:
            abi = _abi(config["abi"])
        except ValueError as error:
            print(error)
            return 3

        w3 = endpoint.get_web3()
        contract = w3.eth.contract(address=config["address"], abi=abi)
        for event in contract.abi:
            if event["type"] == "function":
                args = [[f"{arg['name'].strip('_')}:", arg["type"]] for arg
                        in event.get("inputs")]
                row = [event.get("name"), event.get("stateMutability"),
                       tabulate(args, tablefmt="plain")]
                tabulate_table.append(row)

        print(tabulate(tabulate_table, headers=tabulate_header,
                       tablefmt="grid"))

    def _call(self, card):
        endpoint = self._get_endpoint(card)
        config = get_configuration(card.serial_number)
        try:
            config = config["hidden"]["eth"]["contract"][self.data.alias]
        except KeyError as error:
            print(f'Contract with name {self.data.alias} not found.')
            return -1

        try:
            abi = _abi(config["abi"])
        except ValueError as error:
            print(error)
            return 3

        w3 = endpoint.get_web3()

        contract = w3.eth.contract(address=config["address"], abi=abi)
        try:
            function = contract.get_function_by_name(self.data.function)
        except ValueError as error:
            print(error)
            print("Valid functions are:")
            self._functions(card)
            return 1

        if function.abi["stateMutability"] in ["nonpayable", "payable"]:
            print(
                "For this function you should use Transact as it changes the "
                "state of the network.")
            return 4

        try:
            print(function(*self.data.arguments).call())
        except (TypeError, web3.exceptions.BadFunctionCallOutput) as error:
            print(error)
            return 2
        except web3.exceptions.ContractLogicError as error:
            print(f"Error occurred with execution: {error}")
            return -4

        return 0

    def _transact(self, card):
        endpoint = self._get_endpoint(card)
        self._check(card)

        config = get_configuration(card.serial_number)

        if not config["eth"]["api_key"]:
            print("\nTo use the Ethereum network. Go to https://infura.io. Register and get an "
                  "API key. Set the API key with: eth config api_key")
            return -1

        try:
            contract_config = config["hidden"]["eth"]["contract"][self.data.alias]
        except KeyError as error:
            print(f'Contract "{self.data.alias}" not found.')
            return 2

        try:
            derivation = cryptnoxpy.Derivation[config["eth"]["derivation"]]
        except LookupError:
            print("Derivation value not valid")
            return 1

        try:
            abi = _abi(contract_config["abi"])
        except ValueError as error:
            print(error)
            return 3

        w3 = endpoint.get_web3()
        public_key = card.get_public_key(derivation, path=Eth.PATH, compressed=False)
        contract = w3.eth.contract(address=contract_config["address"], abi=abi)
        try:
            function = contract.get_function_by_name(self.data.function)
        except ValueError as error:
            print(error)
            print("Valid functions are:")
            self._functions(card)
            return 1

        if function.abi["stateMutability"] not in ["nonpayable", "payable"]:
            print("For this function you should use call as it only returns a "
                  "value.")
            return 4

        try:
            set_data = function(*self.data.arguments).buildTransaction()
        except TypeError:
            print("Invalid number of arguments")
            return -3
        except web3.exceptions.ContractLogicError as error:
            print(f"Error occurred with execution: {error}")
            return -4

        price = self.data.price or int(config["eth"]["price"])
        limit = self.data.limit or int(config["eth"]["limit"])

        balance = endpoint.get_balance(wallet.address(public_key))
        if balance - (web3.Web3.fromWei(price, "gwei") * limit) < 0:
            print("Not enough fund for the transaction")
            return -2

        set_data.update({
            "nonce": w3.eth.get_transaction_count(
                wallet.checksum_address(public_key)),
            "gasPrice": price,
            "gas": limit
        })
        set_data = wallet.convert_values(set_data)

        print("\nSigning with the Cryptnox")
        digest = endpoint.transaction_hash(set_data)
        signature = sign(card, digest, derivation, path=Eth.PATH)

        if not signature:
            print("Error in getting signature")
            return -1

        if not Contract._confirm(public_key, contract.address, balance, 0,
                                 price, limit):
            print("Canceled by user")
            return -1

        try:
            transaction = endpoint.push(set_data, signature, public_key)
        except requests.exceptions.RequestException as error:
            print(f"Error occurred in communication with the server: {error}")
            return 3
        except ValueError as error:
            print(error.args[0]["message"])
            return 4

        print(f"Request sent to network. Transaction id: {transaction.hex()}. "
              f"It can take some time until you can see the change.")

        return 0

    @staticmethod
    def _confirm(public_key, address, balance, value, price, limit):
        gas_price = web3.Web3.fromWei(price, "gwei")
        gas = float(gas_price * limit)
        tabulate_table = [
            ["BALANCE:", f"{balance / 10 ** 18}", "ETH", "ON", "ACCOUNT:",
             f"{wallet.checksum_address(public_key)}"],
            ["TRANSACTION:", f"{value}", "ETH", "TO", "CONTRACT:",
             f"{address}"],
            ["MAX GAS:", f"{gas}"],
            ["MAX TOTAL:", f"{gas + value}"]
        ]

        floating_points = max(
            cryptos.wallet_utils.number_of_significant_digits(
                (gas + value)), 8)

        print("\n\n--- Transaction Ready --- \n")
        print(tabulate(tabulate_table, tablefmt='plain',
                       floatfmt=f".{floating_points}f"), "\n")
        conf = input("Confirm ? [y/N] > ")
        return conf.lower() == "y"


class Eth(Command):
    """
    Command for sending payment on Bitcoin and Ethereum networks
    """
    PATH = "m/44'/60'/0'/0"

    _name = enums.Command.ETH.value

    def _execute(self, card) -> int:
        try:
            if self.data.eth_action == "send":
                return self._send(card)
            if self.data.eth_action == "config":
                return create_config_method(card.serial_number,
                                            self.data.key, self.data.value,
                                            "eth")
            if self.data.eth_action == "contract":
                contract = Contract(self.data)
                return contract._execute(card)
        except requests.HTTPError as error:
            if error.response.status_code == 401:
                print("Access denied. Check your API key with: eth config api_key")
            else:
                print(f"There was in issue in communication: {error}")
            return -1
        except requests.RequestException as error:
            print(f"There was in issue in communication: {error}")
            return -1

        return 0

    def _send(self, card) -> int:
        self._check(card)

        config = get_configuration(card.serial_number)["eth"]
        if not config["api_key"]:
            print("\nTo use the Ethereum network. Go to https://infura.io. Register and get an "
                  "API key. Set the API key with: eth config api_key")
            return -1

        try:
            network = wallet.Network[(self.data.network or config["network"]).upper()]
        except KeyError:
            print("Network is invalid")
            return 1

        try:
            derivation = cryptnoxpy.Derivation[config["derivation"]]
        except KeyError:
            print("Derivation is invalid")
            return 1

        price = self.data.price or int(config.get("price", 8))
        limit = self.data.limit or int(config.get("limit", 21000))
        endpoint = wallet.Web3Api(card, network, config.get("api_key", ""))

        print("Sending ETH")
        try:
            # eth path in the current key
            message = self._send_funds(card, derivation, endpoint, self.data.address,
                                       self.data.amount, price, limit)
        except ValueError as error:
            try:
                print(error.args[0].get(
                    "message", "Something went wrong").capitalize())
                return 1
            except (AttributeError, LookupError):
                raise error

        if message.startswith("DONE"):
            print(f"\nTransaction id: {message[6:]}\nBalance might take 30 s to be refreshed.")

        return 0

    @staticmethod
    def _send_funds(card, derivation, endpoint, address, amount, price, limit):
        public_key = card.get_public_key(derivation, path=Eth.PATH, compressed=False)
        card.derive(path=Eth.PATH)
        from_address = wallet.checksum_address(public_key)
        balance = endpoint.get_balance(from_address)
        max_spendable = balance - ((price * limit) * 10 ** 9)
        if amount * 10 ** 18 > max_spendable:
            raise ValueError({"message": "Not enough fund for the tx"})
        balance = balance / 10 ** 18

        sanitized_transaction = dict(
            nonce=endpoint.get_transaction_count(from_address, "pending"),
            gasPrice=price,
            gas=limit,
            to=web3.Web3.toChecksumAddress(address),
            value=web3.Web3.toWei(amount, "ether"),
            data=b''
        )
        print("\nSigning with the Cryptnox")
        sanitized_transaction = wallet.convert_values(sanitized_transaction)
        digest = endpoint.transaction_hash(sanitized_transaction)

        signature = sign(card, digest, derivation, path=Eth.PATH)

        if not signature:
            print("Error in getting signature")
            return -1

        gas = float(web3.Web3.fromWei(price, "gwei") * limit)
        tabulate_table = [
            ["BALANCE:", f"{balance}", "ETH", "ON", "ACCOUNT:",
             f"{wallet.checksum_address(public_key)}"],
            ["TRANSACTION:", f"{amount}", "ETH", "TO", "ACCOUNT:",
             f"{web3.Web3.toChecksumAddress(address)}"],
            ["MAX GAS:", f"{gas}"],
            ["MAX TOTAL:", f"{gas + amount}"]
        ]

        floating_points = cryptos.wallet_utils.number_of_significant_digits(
            (gas + amount))

        print("\n\n--- Transaction Ready --- \n")
        print(tabulate(tabulate_table, tablefmt='plain',
                       floatfmt=f".{floating_points}f"), "\n")
        conf = input("Confirm ? [y/N] > ")
        if conf.lower() != "y":
            return "Canceled by the user."
        return "DONE: " + bytes(endpoint.push(sanitized_transaction, signature, public_key)).hex()

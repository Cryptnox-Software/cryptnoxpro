# -*- coding: utf-8 -*-
"""
Module for creating and adding logic for eosio commands.
"""
import json
import re

import cryptnoxpy
import requests
from tabulate import tabulate

from .command import Command
from .helper.config import create_config_method
from .helper.helper_methods import sign

try:
    import enums
    from config import get_configuration
    from wallet.eos import EOSWallet
    from lib.cryptos.wallet_utils import number_of_significant_digits
except ImportError:
    from .. import enums
    from ..config import get_configuration
    from ..wallet.eos import EOSWallet
    from ..lib.cryptos.wallet_utils import number_of_significant_digits


class Eosio(Command):
    """
    Command to work with eosio network
    """
    DERIVATION = cryptnoxpy.Derivation.DERIVE
    PATH = "m/44'/194'/0'/0"

    _name = enums.Command.EOSIO.value

    class DataValidationException(Exception):
        """
        Exception class for indicating that the data is not valid
        """

    def _execute(self, card) -> int:
        result = -1

        try:
            if self.data.action in ["send", "transfer"]:
                result = self._transfer(card)
            elif self.data.action == "push":
                try:
                    result = self._push(card)
                except EOSWallet.NoAccountsException as error:
                    print(error)
            elif self.data.action == "get":
                result = self._get(card)
            elif self.data.action == "config":
                result = create_config_method(card.serial_number,
                                              self.data.key, self.data.value,
                                              "eosio")
            else:
                print("Action not found")
        except requests.exceptions.RequestException as error:
            print(f"Error with connection: {error}")

        return result

    def _get(self, card) -> int:
        wallet = self._wallet(card)
        result = ""

        if self.data.get == "info":
            result = wallet.var_ce.get_info()
        elif self.data.get == "block":
            result = wallet.var_ce.get_block(self.data.block)
        elif self.data.get == "account":
            print(self.data)
            result = wallet.var_ce.get_account(self.data.account)
        elif self.data.get == "code":
            result = wallet.var_ce.get_code(self.data.account)["code_hash"]
        elif self.data.get == "currency":
            if self.data.currency == "balance":
                balance_list = wallet.var_ce.get_currency_balance(
                    self.data.account, code=self.data.contract,
                    symbol=self.data.symbol)
                result = balance_list[0] if len(
                    balance_list) == 1 else balance_list
            elif self.data.currency == "stats":
                result = wallet.var_ce.get_currency()
        elif self.data.get == "accounts":
            result = wallet.var_ce.get_accounts(self.data.public_key)
        elif self.data.get == "servants":
            try:
                result = wallet.var_ce.get_servants(self.data.account)
            except json.decoder.JSONDecodeError as error:
                print(f"Error in response {error}")
                return 1
        elif self.data.get == "transaction":
            result = wallet.var_ce.get_transaction(self.data.txid)
        elif self.data.get == "pubkey":
            return self._print_public_key(card)
        else:
            print("Command not found")
            return -1
        print(json.dumps(result, indent=2))

        return 0

    def _push(self, card) -> int:
        if self.data.push == "action":
            trx = Eosio._get_processed_json_argument(self.data.data)
        elif self.data.push == "transaction":
            trx = Eosio._get_processed_json_argument(self.data.transaction)
        else:
            print("Action not found")
            return -1

        try:
            data = json.loads(trx)
            if isinstance(data, str):
                print(f"Error in json: Must be object")
                return -1
        except json.decoder.JSONDecodeError as error:
            print(f"Error in json: {error}")
            return -1

        wallet = self._wallet(card)

        if self.data.push == "action":
            try:
                account = wallet.choose_account()
            except EOSWallet.ExitException:
                print("Canceled by the user.")
                return 0

            data = [account, self.data.contract, self.data.action_name, trx]
            action = wallet.push_action
        elif self.data.push == "transaction":
            data = [trx]
            action = wallet.push

        try:
            transaction = action(*data)
        except (LookupError, TypeError):
            print("ERROR : Provided JSON is not valid")
            return 1
        except ValueError:
            print("There was an issue in processing the JSON into request to "
                  "the server.")
            return 2

        return self._process(card, wallet, transaction)

    def _transfer(self, card) -> int:
        wallet = self._wallet(card)

        try:
            account = self.data.account
        except AttributeError:
            try:
                account = wallet.choose_account()
            except EOSWallet.ExitException:
                print("Canceled by the user")
                return 0

        to_account = self.data.recipient
        memo = self.data.memo
        amount = self.data.amount
        balance = float(wallet.get_balance().split(" " + wallet.coin_symbol)[0])

        if amount > balance:
            print("Not enough fund for the tx")
            return 1

        print("\nSignature in progress...")

        transaction = wallet.send(account, to_account, amount, memo)
        tabulate_table = [
            ["BALANCE:", f"{balance}", "ETH", "ON", "ACCOUNT:",
             f"{account}"],
            ["TRANSACTION:", f"{amount}", "ETH", "TO", "ACCOUNT:",
             f"{to_account}"]
        ]

        floating_points = max([number_of_significant_digits(balance),
                               number_of_significant_digits(amount)])

        return self._process(card, wallet, transaction,
                             tabulate(tabulate_table, tablefmt='plain',
                                      floatfmt=f".{floating_points}f"))

    @staticmethod
    def _process(card, wallet, transaction, additional_info=""):
        key_type = cryptnoxpy.KeyType[wallet.key_type]
        config = get_configuration(card.serial_number)["eosio"]
        try:
            derivation = cryptnoxpy.Derivation[config["derivation"]]
        except KeyError as error:
            raise Eosio.DataValidationException("Derivation error.") from error

        public_key = card.get_public_key(derivation, key_type,
                                         path=Eosio.PATH, compressed=False)

        digest = wallet.var_ce.transaction_hash(transaction)
        signature = sign(card, bytes.fromhex(digest), derivation, key_type, Eosio.PATH, True)

        if not signature:
            print("Error in getting signature")
            return -1

        print("\n\n--- Transaction Ready --- \n")
        if additional_info:
            print(additional_info, "\n")
        conf = input("Confirm ? [y/N] > ")
        if conf.lower() != "y":
            print("Canceled by the user")
            return 0

        tx_info = wallet.var_ce.push(transaction, public_key, signature, wallet.key_type)

        try:
            print(f"\nTransaction id: {tx_info['transaction_id']}")
        except TypeError:
            print("Error tx :")
            print(tx_info)

        return 0

    @staticmethod
    def _get_processed_json_argument(data: str) -> str:
        result = data
        if isinstance(result, list):
            result = " ".join(result)
        result = result.strip("'")
        result = re.sub(r"(\w+):", r'"\1":', result)
        result = re.sub(r"(:\s)((?!false|true)\d*\.?\d*\s?[a-zA-Z\.]+\d*)([,\s\}])",
                        r'\1"\2"\3', result)
        result = re.sub(r'(:.?)(")([,\s])', r'\1\2"\3', result)
        result = re.sub(r'(:\s?)([,\}\]])', r'\1""\2', result)

        return result

    def _print_public_key(self, card: cryptnoxpy.Card):
        config = get_configuration(card.serial_number)["eosio"]
        endpoint = config["endpoint"]

        try:
            key_type = cryptnoxpy.KeyType[self.data.key_type or config["key_type"]]
        except KeyError as error:
            raise Eosio.DataValidationException("Key type can be only K1 or R1.") from error

        try:
            derivation = cryptnoxpy.Derivation[config["derivation"]]
        except KeyError as error:
            raise Eosio.DataValidationException("Derivation error.") from error

        coin_symbol = config.get("coin_symbol", "EOS")
        public_key = card.get_public_key(derivation, key_type, Eosio.PATH)
        wallet = EOSWallet(public_key, endpoint, coin_symbol, key_type.name)

        print(f"Public key: {wallet.address}")

        return 0

    def _wallet(self, card) -> EOSWallet:
        self._check(card)

        path = self.data.path
        config = get_configuration(card.serial_number)["eosio"]
        endpoint = self.data.url or config.get(
            "endpoint", "https://jungle3.eossweden.org")
        coin_symbol = self.data.symbol or config.get("coin_symbol", "EOS")

        try:
            key_type = cryptnoxpy.KeyType[self.data.key_type or config["key_type"]]
        except KeyError as error:
            raise Eosio.DataValidationException("Key type can be only K1 or R1.") from error

        try:
            derivation = cryptnoxpy.Derivation[config["derivation"]]
        except KeyError as error:
            raise Eosio.DataValidationException("Derivation error.") from error

        public_key = card.get_public_key(derivation, key_type, path)

        wallet = EOSWallet(public_key, endpoint, coin_symbol, key_type.name)
        card.derive(key_type, path=path)

        return wallet

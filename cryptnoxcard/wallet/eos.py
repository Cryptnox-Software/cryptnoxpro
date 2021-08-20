# -*- coding: utf-8 -*-
"""
A basic EOS wallet library
"""

import datetime as dt
import hashlib
import json
from decimal import Decimal
from typing import Dict, Any

import cryptnoxpy
import pytz
from tabulate import tabulate

from .validators import EnumValidator, UrlValidator

try:
    from lib.eospy import cleos
    from lib import cryptos
except ImportError:
    from ..lib.eospy import cleos
    from ..lib import cryptos


def bin_to_b58eosio(inp, key_type: str) -> str:
    """

    :param inp:
    :param key_type: str (e.g. K1)
    :return: str
    """
    leading_z_bytes = 0
    for var_x in inp:
        if var_x != 0:
            break
        leading_z_bytes += 1
    checksum = hashlib.new('ripemd160',
                           inp + bytes(key_type, "ascii")).digest()[:4]
    return '1' * leading_z_bytes + \
           cryptos.py3specials.changebase(inp + checksum, 256, 58)


def pubkey2adr(pub_key_hex: str, key_type: str) -> str:
    """

    :param pub_key_hex: hexadecimal public address
    :param key_type: type of key (e.g. K1)
    :return: public address
    """
    return "PUB_" + key_type + "_" + bin_to_b58eosio(bytes.fromhex(pub_key_hex),
                                                     key_type)


class EOSWallet:
    """
    EOSWallet
    """

    class NoAccountsException(Exception):
        """
        Exception class for indicating that there are no accounts attached to
        given public key
        """

    class ExitException(Exception):
        """
        Exception class for indicating that user has entered exit
        """

    def __init__(self, public_key, api, coin_symbol: str = "EOS", key_type: str = "K1"):
        """

        :param pubkey:
        :param api:
        :param card:
        :param coin_symbol:
        :param key_type:
        """
        self.api = api
        self.coin_symbol = coin_symbol
        self.var_ce = cleos.Cleos(url=api)
        self.key_type = key_type
        self.address = self.get_address(public_key)

    def get_address(self, pub_key: str) -> str:
        """

        :param pub_key: type of key (e.g. K1)
        :return: public address
        """
        return pubkey2adr(pub_key, self.key_type)

    def get_account(self):
        """
curl --header "Content-Type: application/json" --request POST --data '{"public_key":"PUB_K1_6iAMvpi8pk9KybiiNY27Kyy4fK1R9qx3TZJBKg8gwLNTXYDvkH"}' https://jungle3.eossweden.org/v1/history/get_key_accounts
        :return:
        """
        acci = self.var_ce.get_accounts(self.address)
        return acci["account_names"]

    def get_balance(self, account_index: int = 0) -> str:
        """

        :return: str
        """
        try:
            bal = self.var_ce.get_currency_balance(
                self.get_account()[account_index])
        except IndexError:
            bal = ""
        if len(bal) > 0:
            return bal[0]

        return "0 EOS"

    def create_account(self, account_name: str, from_account: str, pv_key: str) \
            -> None:
        """

        :param account_name: str
        :param from_account: str
        :param pv_key: str
        :return: None
        """
        self.var_ce.create_account(from_account, pv_key, account_name,
                                   self.address, self.address)

    def choose_account(self) -> str:
        """
        Prompts user to choose Eosio account

        :return: Name of the account user chose
        :rtype: str
        :raise EOSWallet.NoAccountsException: No accounts are found for pubkey
        :raise EOSWallet.ExitException: User has input exit
        """
        accounts = self.get_account()
        if not accounts:
            raise EOSWallet.NoAccountsException(
                "No account were found registered to "
                "the public key on the card")
        choice = accounts[0]
        if len(accounts) > 1:
            tabulate_data = [
                [index + 1, value, self.get_balance(index)]
                for index, value in enumerate(accounts)]
            headers = ["", "ACCOUNT", "BALANCE"]
            print(f"\n{tabulate(tabulate_data, headers=headers)}\n")
            while True:
                choice = input(f"Choose account you want to use "
                               f"(1 - {len(accounts)}):").strip()
                if choice == "exit":
                    raise EOSWallet.ExitException()
                try:
                    choice = accounts[int(choice) - 1]
                except (ValueError, LookupError):
                    pass
                else:
                    break
                print("\nInvalid choice")
        return choice

    def push(self, trx_str: str) -> Dict[str, Any]:
        """

        :param trx_str: str
        :return: str
        """
        trx = json.loads(trx_str)
        # Converting payload to binary
        act_idx = 0
        for action in trx['actions']:
            data_b = self.var_ce.abi_json_to_bin(action['account'],
                                                 action['name'],
                                                 action['data'])
            # Inserting payload binary form as "data" field in original payload
            trx['actions'][act_idx]['data'] = data_b['binargs']
            act_idx += 1
        # final transaction formed
        trx['expiration'] = str((dt.datetime.utcnow()
                                 + dt.timedelta(seconds=60))
                                .replace(tzinfo=pytz.UTC))
        return trx

    def push_action(self, account: str, contract: str, action: str,
                    data: str) -> Dict[str, Any]:
        """

        :param str account:
        :param str contract:
        :param str action:
        :param str data:
        :return: Result of action
        """
        trx_data = json.loads(data)

        payload = {
            "account": contract,
            "name": action,
            "authorization": [{
                "actor": account,
                "permission": "active",
            }],
        }
        # Converting payload to binary
        data_b = self.var_ce.abi_json_to_bin(contract, action, trx_data)
        # Inserting payload binary form as "data" field in original payload
        payload['data'] = data_b['binargs']
        # final transaction formed
        trx = {
            "actions": [payload],
            "expiration": str((dt.datetime.utcnow() + dt.timedelta(seconds=60))
                              .replace(tzinfo=pytz.UTC))
        }
        return trx

    def send(self, from_account: str, to_account: str, amount: str,
             memo: str = "") -> Dict[str, Any]:
        """

        :param from_account: str
        :param to_account: str
        :param amount: str (ffff SYMB)
        :param memo: str
        :return: str
        """
        amount = '%.4f %s' % (Decimal(amount), self.coin_symbol)
        arguments = {
            "from": from_account,  # sender
            "to": to_account,  # receiver
            "quantity": amount,
            "memo": memo,
        }
        payload = {
            "account": "eosio.token",
            "name": "transfer",
            "authorization": [{
                "actor": from_account,
                "permission": "active",
            }],
        }
        # Converting payload to binary
        data_b = self.var_ce.abi_json_to_bin(payload['account'],
                                             payload['name'],
                                             arguments)
        # Inserting payload binary form as "data" field in original payload
        payload['data'] = data_b['binargs']
        # final transaction formed
        trx = {
            "actions": [payload],
            "expiration": str((dt.datetime.utcnow() + dt.timedelta(seconds=60))
                              .replace(tzinfo=pytz.UTC))
        }
        return trx


class EosioValidator:
    """
    Class defining Eosio validators
    """
    endpoint = UrlValidator()
    key_type = EnumValidator(cryptnoxpy.KeyType)
    derivation = EnumValidator(cryptnoxpy.Derivation)

    def __init__(self, endpoint: str = "https://api.jungle3.alohaeos.com",
                 key_type: int = "K1", derivation: str = "DERIVE"):
        self.endpoint = endpoint
        self.key_type = key_type
        self.derivation = derivation

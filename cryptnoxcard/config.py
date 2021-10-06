# -*- coding: utf-8 -*-
"""
Module for handling config file
"""
import gzip
import json
from typing import (
    Any,
    Dict
)

import cryptnoxpy

try:
    from command.helper import helper_methods
except ImportError:
    from .command.helper import helper_methods

_CONFIGURATION = {}


def get_default_configuration() -> Dict:
    """
    Returns default configuration to be used

    :return: Default configuration
    :rtype: dict
    """
    config = {
        "btc": {
            "derivation": "DERIVE",
            "fees": "2000",
            "network": "testnet",
        },
        "eth": {
            "api_key": "",
            "derivation": "DERIVE",
            "endpoint": "cryptnox",
            "limit": "30000",
            "network": "ropsten",
            "price": "8",
        },
        "eosio": {
            "coin_symbol": "EOS",
            "derivation": "DERIVE",
            "endpoint": "https://jungle3.cryptolions.io:443",
            "key_type": "K1",
        },
        "hidden": {
            "eth": {
                "contract": {}
            }
        }
    }

    return config


def get_configuration(card: cryptnoxpy.Card) -> Dict:
    """
    Get the configuration.

    :param cryptnoxpy.Card card: Serial number of the card used

    :return: Configuration from file or default configuration if not found
    :rtype: dict
    """
    try:
        config = _CONFIGURATION[card.serial_number]
    except LookupError:
        config = read_card_config(card)

        _CONFIGURATION[card.serial_number] = config

    return config


def save_to_config(card: cryptnoxpy.Card, config: Dict[str, Any]) -> None:
    """
    Save given configuration to file.

    :param cryptnoxpy.Card card: Serial number of the card used
    :param Dict[str, Any] config: Configuration to save
    """
    _CONFIGURATION[card.serial_number] = config

    card.user_data = gzip.compress(bytes(json.dumps(config), "UTF-8"))


def read_card_config(card: cryptnoxpy.Card) -> Dict:
    """
    Reads the configuration.

    :param cryptnoxpy.Card card: Serial number of the card used

    :return: Configuration read from the file
    :rtype: dict
    """

    config = get_default_configuration()
    try:
        card_config = json.loads(gzip.decompress(card.user_data))
    except (json.decoder.JSONDecodeError, FileNotFoundError, gzip.BadGzipFile):
        save_to_config(card, config)
    else:
        helper_methods.deep_update(config, card_config)

    return config


def get_cached_serials():
    return _CONFIGURATION.keys()

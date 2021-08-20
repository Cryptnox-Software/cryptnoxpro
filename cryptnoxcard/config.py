# -*- coding: utf-8 -*-
"""
Module for handling config file
"""
import gzip
import json
from pathlib import Path
from typing import Union, Dict

from appdirs import user_data_dir

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
            "network": "testnet",
            "fees": "2000",
            "derivation": "DERIVE"
        },
        "eosio": {
            "endpoint": "https://jungle3.cryptolions.io:443",
            "coin_symbol": "EOS",
            "key_type": "K1",
            "derivation": "DERIVE"
        },
        "eth": {
            "network": "ropsten",
            "price": "8",
            "limit": "30000",
            "derivation": "DERIVE",
            "api_key": ""
        },
        "hidden": {
            "eth": {
                "contract": {}
            }
        }
    }

    return config


def get_configuration(card_serial: Union[int, str]) -> Dict:
    """
    Get the configuration.

    :param card_serial: Serial number of the card used
    :return: Configuration from file or default configuration if not found
    :rtype: dict
    """
    try:
        config = _CONFIGURATION[str(card_serial)]
    except LookupError:
        config = read_card_config(card_serial)

        _CONFIGURATION[card_serial] = config

    return config


def return_config_path(card_serial: Union[int, str]) -> Path:
    """
    Returns path of config file.

    :param card_serial: Serial number of the card used
    :return: Path of the configuration file
    :rtype: Path
    """
    config_path = Path(user_data_dir("CryptnoxCard", False))
    config_path = config_path.joinpath(str(card_serial))
    config_path.mkdir(parents=True, exist_ok=True)
    config_path = config_path.joinpath("cryptnoxcard.json.gz")

    return config_path


def save_to_config(card_serial: Union[int, str]
                   ,
                   config: Dict) -> None:
    """
    Save given configuration to file.

    :param card_serial: Serial number of the card used
    :param Dict config: Configuration to save
    """
    _CONFIGURATION[card_serial] = config

    with gzip.open(return_config_path(card_serial), 'wb') as file:
        file.write(bytes(json.dumps(config), "UTF-8"))


def read_card_config(card_serial: Union[int, str]) -> Dict:
    """
    Reads configuration from config file.

    :param card_serial: Serial number of the card used
    :return: Configuration read from the file
    :rtype: dict
    """

    path = return_config_path(card_serial)
    config = get_default_configuration()
    try:
        with gzip.open(path, "rb") as file:
            card_config = json.loads(file.read())
    except FileNotFoundError:
        save_to_config(card_serial, config)
    else:
        helper_methods.deep_update(config, card_config)

    return config


def get_cached_serials():
    return _CONFIGURATION.keys()

"""
Module for managing cryptocurrency-specific configurations including
network settings, API keys, and validation for Bitcoin and Ethereum
wallet configurations.
"""

from typing import Union

import cryptnoxpy

try:
    from config import (
        get_configuration,
        save_to_config
    )
    from wallet.validators import ValidationError
    from wallet.btc import BlkHubApi
except ImportError:
    from ...config import (
        get_configuration,
        save_to_config
    )
    from ...wallet.validators import ValidationError
    from ...wallet.btc import BlkHubApi


def add_config_sub_parser(sub_parser, crypto_currency: str) -> None:
    """
    Add config subparser

    :param sub_parser: Parser object to be added to
    :param crypto_currency: Name of the cryptocurrency
    :return: None
    """
    parser = sub_parser.add_parser("config",
                                   help=f"View or edit {crypto_currency} "
                                   "configuration")
    parser.add_argument("key", nargs="?", type=str, default=None,
                        help="Define key to use")
    parser.add_argument("value", nargs="?", type=str, default=None,
                        help="Define a new value for the given section "
                             "and key")


def create_config_method(card: cryptnoxpy.Card, key: Union[str, None], value: Union[str, None],
                         currency_name: str) -> int:
    """
    Create config method for specific cryptocurrency

    :param cryptnoxpy.Card card: Card to use for the operation
    :param key: Key of the configuration dictionary to be edited
    :param value: Value to be inserted into configuration or None
    :param currency_name: Name of the crypto for which to create
                          configuration

    :return:
    :rtype: int
    """
    if value is not None:
        return write_config(card, currency_name, key, value)
    if key is not None:
        return print_key_config(card, currency_name, key)

    return print_section_config(card, currency_name)


def print_config(card: cryptnoxpy.Card, exclude=None) -> None:
    """
    Prints contents of config.

    :param cryptnoxpy.Card card: Card to use for the operation
    :param Dict exclude: Exclude section from printing
    """
    exclude = exclude or ["hidden"]
    config = get_configuration(card)

    for section in config:
        if section in exclude:
            continue
        print(f"\n[{section.upper()}]")
        for key, value in config[section].items():
            print(f"{key}: {value}" + find_endpoint(section, key, value, " - Read only"))


def print_section_config(card: cryptnoxpy.Card, section: str) -> int:
    """
    Prints contents of a section from configuration.

    :param cryptnoxpy.Card card: Card to use for the operation
    :param section: Section of the configuration file wanted printed

    :return: Execution status
    :rtype: int
    """
    config = get_configuration(card)
    if section not in config:
        print("No such section")
        return 1

    print(f"[{section.upper()}]")

    for key, value in config[section].items():
        print(f"{key}: {value}" + find_endpoint(section, key, value, " - YOU CAN'T EDIT THIS"))

    return 0


def print_key_config(card: cryptnoxpy.Card, section: str, key: str) -> int:
    """
    Prints key and value from section in config.

    :param cryptnoxpy.Card card: Card to use for the operation
    :param section: Section of the configuration file wanted printed
    :param key: Name of the parameter we want to change

    :return: Execution status
    :rtype: int
    """
    config = get_configuration(card)
    try:
        old_key = key
        key = "network" if key == "endpoint" and section != "eosio" else key
        value = config[section][key]
        endpoint = find_endpoint(section, key, value, " - YOU CAN'T EDIT THIS")
        if old_key == "endpoint" and section != "eosio":
            print(endpoint)
        else:
            print(f"{key}: {value}")

    except LookupError:
        print("No such section or key")
        return 1

    return 0


def find_endpoint(section: str, key: str, value: str, append: str = "") -> str:
    if key == "network" and section == "btc":
        return f"\nendpoint: {BlkHubApi.get_api(value)}{append}"

    return ""


def write_config(card: cryptnoxpy.Card, section: str, key: str, value: str) -> int:
    """
    Writes new value at chosen section and key.

    :param cryptnoxpy.Card card: Card to use for the operation
    :param section: Section of the config file to write to
    :param key: Name of the parameter we want to change
    :param value: Value we want to insert into the configuration file

    :return: Execution status
    :rtype: int
    """
    config = get_configuration(card)
    try:
        instance = eval(f"{section.capitalize()}Validator")()
    except NameError:
        print("Invalid section")
        return 1
    try:
        getattr(instance, key)
        setattr(instance, key, value)
        instance.validate()
    except ValidationError as error:
        valid = instance.__class__.__dict__[key]
        print(f"Invalid value for the {key.replace('_', ' ')}")
        if valid:
            if valid.valid_values:
                print("Valid values are:")
                print(valid.valid_values)
            else:
                print(error)
        return 1
    except AttributeError:
        pass

    try:
        config[section][key] = str(getattr(instance, key))
    except AttributeError:
        try:
            config[section][key]
        except LookupError:
            print("Invalid key")
            return 1

    save_to_config(card, config)
    print("\nConfiguration is written into the config file")

    return 0

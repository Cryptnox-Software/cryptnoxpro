#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Command line interface for Cryptnox Cards
"""
import lazy_import
import sys

import argparse

try:
    from command import options
    from command import factory
    from __init__ import __version__
    import interactive_cli
except ImportError:
    from .command import options
    from .command import factory
    from . import interactive_cli
    from . import __version__

cryptnoxpy = lazy_import.lazy_module("cryptnoxpy")
json = lazy_import.lazy_module("json")
re = lazy_import.lazy_module("re")
tabulate = lazy_import.lazy_callable("tabulate.tabulate")
requests = lazy_import.lazy_module("requests")
web3 = lazy_import.lazy_module("web3")

APPLICATION_NAME = "CryptnoxCard"


def get_parser() -> argparse.ArgumentParser:
    """
    Get the parser that can be used to process user input

    :return: Argument parser to use for prcessing the user input
    :rtype: argparse.ArgumentParser
    """
    parser = interactive_cli.ErrorParser(description="Cryptnox command line interface.")

    parser.add_argument("-v", "--version", action="version",
                        version=f"Cryptnox Card {__version__}")
    parser.add_argument("--verbose", action="store_true",
                        help="Turn on logging")
    serial_index_parser = parser.add_mutually_exclusive_group()
    serial_index_parser.add_argument("-s", "--serial", type=int,
                                     help="Serial number of the card to be"
                                          " used for the"
                                          " command")

    options.add(parser)

    return parser


def execute(args: argparse.Namespace) -> int:
    command_factory = factory.Factory(args)
    command = command_factory.get_command()
    result = command.execute()

    return result


def main() -> int:
    """
    Main method to call when the script is executed on the comman line

    :return: 0 if the command executed without issues. Other number
             indicating and issue
    :rtype: int
    """
    parser = get_parser()

    try:
        if sys.argv[1] == "cleos":
            sys.argv[1] = "eosio"
    except LookupError:
        pass
    args = parser.parse_args()

    result = 0
    if args.command:
        result = execute(args)
    else:
        cli = interactive_cli.InteractiveCli(__version__, args.verbose)
        cli.run()

    return result


if __name__ == "__main__":
    sys.exit(main())

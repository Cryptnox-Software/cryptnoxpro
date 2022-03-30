#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Command line interface for Cryptnox Cards
"""
import lazy_import
import sys

import argparse

try:
    from __init__ import __version__
    import interactive_cli
    from command import (
        factory,
        options
    )
except ImportError:
    from . import __version__
    from . import interactive_cli
    from .command import (
        factory,
        options
    )

cryptnoxpy = lazy_import.lazy_module("cryptnoxpy")
json = lazy_import.lazy_module("json")
re = lazy_import.lazy_module("re")
tabulate = lazy_import.lazy_callable("tabulate.tabulate")
requests = lazy_import.lazy_module("requests")
web3 = lazy_import.lazy_module("web3")

APPLICATION_NAME = "Cryptnox Pro"


def get_parser() -> argparse.ArgumentParser:
    """
    Get the parser that can be used to process user input

    :return: Argument parser to use for processing the user input
    :rtype: argparse.ArgumentParser
    """
    parser = interactive_cli.ErrorParser(description="Cryptnox command line interface.")

    parser.add_argument("-v", "--version", action="version", version=f"Cryptnox Pro {__version__}")
    parser.add_argument("--verbose", action="store_true", help="Turn on logging")
    parser.add_argument('--port', nargs='?', type=int, default=None, help='Define port to enable remote feature')
    serial_index_parser = parser.add_mutually_exclusive_group()
    serial_index_parser.add_argument("-s", "--serial", type=int,
                                     help="Serial number of the card to be used for the command")

    options.add(parser)

    return parser


def main() -> int:
    """
    Main method to call when the script is executed on the command line

    :return: 0 if the command executed without issues. Other number indicating and issue
    :rtype: int
    """
    parser = get_parser()

    try:
        if sys.argv[1] == "cleos":
            sys.argv[1] = "eosio"
    except LookupError:
        pass
    args = parser.parse_args()

    if args.command:
        result = factory.command(args).execute()
    else:
        print(f'Port: {args.port}')
        result = interactive_cli.InteractiveCli(__version__, args.verbose,args.port).run()

    return result


if __name__ == "__main__":
    sys.exit(main())

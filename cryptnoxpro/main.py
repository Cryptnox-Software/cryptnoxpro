#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Command line interface for Cryptnox Cards
"""
import sys
import traceback
from os import makedirs
from pathlib import Path

import argparse
import lazy_import
from appdirs import user_log_dir

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
    parser.add_argument('--port', nargs='?', type=int, default=None,
                        help='Define port to enable remote feature')
    serial_index_parser = parser.add_mutually_exclusive_group()
    serial_index_parser.add_argument("-s", "--serial", type=int,
                                     help="Serial number of the card to be used for the command")

    options.add(parser)

    return parser


def execute(args):
    if args.command:
        result = factory.command(args).execute()
    else:
        print(f'Port: {args.port}')
        result = interactive_cli.InteractiveCli(__version__, args.verbose, args.port).run()

    return result


def main() -> int:
    """
    Main method to call when the script is executed on the command line

    :return: 0 if the command executed without issues. Other number indicating and issue
    :rtype: int
    """
    parser = get_parser()

    args = parser.parse_args()

    try:
        return execute(args)
    except KeyboardInterrupt:
        return 0
    except Exception:
        print("This is something we haven't foreseen. Please, help us in making the application "
              "better by reporting this issue.")
        traceback.print_exc()
        path = Path(user_log_dir('cryptnoxpro', 'cryptnox'))
        makedirs(path, exist_ok=True)
        error_file = path.joinpath("error.log")
        try:
            with open(error_file, "w") as log:
                traceback.print_exc(file=log)
        except Exception:
            print("Please, copy this error and send it to us, so that we can make the application "
                  "better.")
        else:
            print(f"Error has been also saved into file {error_file}. "
                  "Please, send it to us, so that we can make the application better.")

        input("Press enter to exit application")

        return -1


if __name__ == "__main__":
    sys.exit(main())

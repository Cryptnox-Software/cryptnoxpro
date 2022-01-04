from decimal import Decimal

import argparse

from .. import options as base
from ..options.common import add_pin_option

try:
    import enums
except ImportError:
    from .... import enums


def _validate(address: str) -> str:
    try:
        int(address, 16)
    except ValueError:
        raise argparse.ArgumentTypeError("Not a valid ETH address")

    if not (address.startswith("0x") and len(address) in (40, 42)):
        raise argparse.ArgumentTypeError("Not a valid ETH address")

    return address


def add(parser, interactive: bool = False):
    subparsers = parser.add_subparsers(dest="command", help="Command options")

    base.eth.options(subparsers, interactive)
    _transfer(subparsers, interactive)
    base.info_options(subparsers, interactive)
    base.history_options(subparsers, interactive)

    base.card_configuration(subparsers, interactive)
    base.change_pin_options(subparsers, interactive)
    base.change_puk_options(subparsers, interactive)
    base.unlock_pin_options(subparsers, interactive)

    base.list_options(subparsers, interactive)

    base.initialize_options(subparsers, interactive)
    _seed_options(subparsers, interactive)
    base.reset_options(subparsers, interactive)

    if interactive:
        use_sub_parser = subparsers.add_parser("use", help="Change card to be used by default")
        use_sub_parser.add_argument("serial_index", type=int, nargs="?",
                                    help="Serial number or index of card to be used")
        subparsers.add_parser("exit", help="Full application exit")

    return subparsers


def _seed_options(subparsers, interactive_mode):
    sub_parser = subparsers.add_parser(enums.Command.SEED.value, help="Generate seed for the card")

    if interactive_mode:
        add_pin_option(sub_parser)

    action_sub_parser = sub_parser.add_subparsers(dest="action", required=True)

    action_sub_parser.add_parser("chip", help="Generate new root key in the chip.")
    action_sub_parser.add_parser("dual", help="Generate same seed on two cards. "
                                              "(Requires two cards)")


def _transfer(subparsers, interactive_mode):
    sub_parser = subparsers.add_parser(enums.Command.TRANSFER.value, help="Transfer tokens")

    if interactive_mode:
        add_pin_option(sub_parser)

    sub_parser.add_argument("address", type=_validate, help="Address where to send funds")
    sub_parser.add_argument("amount", type=Decimal, help="Amount to send")
    sub_parser.add_argument("--price", type=int, help="Gas price")
    sub_parser.add_argument("--limit", type=int, help="Gas limit")
from .. import options as base

def add(parser, interactive: bool = False):
    subparsers = parser.add_subparsers(dest="command", help="Command options")

    base.btc_options(subparsers, interactive)
    base.eth.options(subparsers, interactive)
    base.eosio.options(subparsers, interactive)
    base.info_options(subparsers, interactive)
    base.history_options(subparsers, interactive)
    base.config_options(subparsers, interactive)

    base.card_configuration(subparsers, interactive)
    base.change_pin_options(subparsers, interactive)
    base.change_puk_options(subparsers, interactive)
    base.user_key_options(subparsers, interactive)
    base.unlock_pin_options(subparsers, interactive)

    base.list_options(subparsers, interactive)

    base.initialize_options(subparsers, interactive)
    base.seed_options(subparsers, interactive)
    base.reset_options(subparsers, interactive)

    if interactive:
        use_sub_parser = subparsers.add_parser("use", help="Change card to be used by default")
        use_sub_parser.add_argument("serial_index", type=int, nargs="?",
                                    help="Serial number or index of card to be used")
        subparsers.add_parser("exit", help="Full application exit")

    return subparsers
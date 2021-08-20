from .common import (
    add_config_sub_parser,
    add_pin_option
)

try:
    import enums
except ImportError:
    from ... import enums


def _add_get_sub_parser(sub_parser):
    get_parser = sub_parser.add_parser("get", help="Get information from "
                                                   "the network and "
                                                   "display it in JSON "
                                                   "format.")
    get_subparsers = get_parser.add_subparsers(dest="get", required=True,
                                               description="Type of object "
                                                           "to get")
    get_block = get_subparsers.add_parser("block")
    get_block.add_argument("block", type=str, action="store",
                           help="The number or ID of the block to retrieve")
    get_acc = get_subparsers.add_parser("account")
    get_acc.add_argument("account", type=str, action="store",
                         help="The name of the account to retrieve")
    get_code = get_subparsers.add_parser("code")
    get_code.add_argument("account", type=str, action="store",
                          help="The name of the account whose code "
                               "should be retrieved")

    get_accs = get_subparsers.add_parser("accounts")
    get_accs.add_argument("public_key", type=str, action="store",
                          help="The public key to retrieve accounts for")

    get_currency = get_subparsers.add_parser("currency")
    get_curr_subparsers = get_currency.add_subparsers(dest="currency",
                                                      required=True,
                                                      help="Type of "
                                                           "currency "
                                                           "information to "
                                                           "get")
    get_currency_balance = get_curr_subparsers.add_parser("balance")
    get_currency_balance.add_argument("contract", type=str, action="store",
                                      help="The contract that operates the "
                                           "currency")
    get_currency_balance.add_argument("account", type=str, action="store",
                                      help="The account to query balances")
    get_currency_balance.add_argument("symbol", type=str, action="store",
                                      nargs="?", default="EOS",
                                      help="The symbol for the currency "
                                           "if the contract operates "
                                           "multiple currencies.")

    get_currency_stats = get_curr_subparsers.add_parser("stats")
    get_currency_stats.add_argument("contract", type=str, action="store",
                                    help="The contract that operates the "
                                         "currency")
    get_currency_stats.add_argument("symbol", type=str, action="store",
                                    nargs="?", default="EOS",
                                    help="The symbol for the currency if "
                                         "the contract operates multiple "
                                         "currencies"
                                    )

    get_subparsers.add_parser("info")

    get_subparsers.add_parser("pubkey")

    get_transaction = get_subparsers.add_parser("transaction")
    get_transaction.add_argument("txid", type=str, action="store",
                                 help="ID of the transaction to retrieve")

    get_servants = get_subparsers.add_parser("servants")
    get_servants.add_argument("account", type=str, action="store",
                              help="Reference account to return accounts created by this "
                                   "account")

def _add_push_sub_parser(sub_parser):
    push_parser = sub_parser.add_parser("push", help="Push action or transaction to the "
                                                     "selected network")
    push_subparsers = push_parser.add_subparsers(dest="push", required=True,
                                                 description="Action to push")
    push_action = push_subparsers.add_parser("action", help="Execute an action on the "
                                                            "contract.")
    push_action.add_argument("contract", type=str, action="store",
                             help="Target contract of the action")
    push_action.add_argument("action_name", type=str, action="store",
                             help="The action name to execute on the contract")
    push_action.add_argument("data", type=str, action="store", nargs="+",
                             help="JSON string of the arguments to the contract")
    push_transaction = push_subparsers.add_parser("transaction", help="Push a transaction to "
                                                                      "the network.")
    push_transaction.add_argument("transaction", type=str, action="store", nargs="+",
                                  help="Transaction to push")

def _add_transfer_sub_parser(sub_parser, name: str, sender: bool, help_text: str):
    transfer_sub_parser = sub_parser.add_parser(name, help=help_text)
    if sender:
        transfer_sub_parser.add_argument("sender", type=str, action="store",
                                         help="The account sending tokens")
    transfer_sub_parser.add_argument("recipient", type=str, action="store",
                                     help="The account receiving tokens")
    transfer_sub_parser.add_argument("amount", type=float, action="store",
                                     help="The amount of tokens to send")
    transfer_sub_parser.add_argument("memo", type=str, action="store", nargs="?", default="",
                                     help="The memo for the transfer")

def options(subparsers, pin_option: bool):
    sub_parser = subparsers.add_parser(enums.Command.EOSIO.value, help="EOSIO commands")
    sub_parser.add_argument("-u", "--url", metavar="URL", type=str, nargs="?",
                            help="URL of the API node")
    sub_parser.add_argument("-k", "--key_type", choices=["K1, R1"], help="Key type.")
    sub_parser.add_argument("-P", "--path", metavar="path", type=str, nargs="?",
                            default="m/44'/194'/0'/0", help="BIP32 path from Cryptnox seed for the"
                                                            " EC keypair")
    sub_parser.add_argument("-s", "--symbol", metavar="coin_symbol", type=str, nargs="?",
                            help="Coin symbol")

    if pin_option:
        add_pin_option(sub_parser)

    action_sub_parser = sub_parser.add_subparsers(dest="action", required=True)

    _add_transfer_sub_parser(action_sub_parser, "send", False, "Simple command to send EOSIO "
                                                               "system token")
    _add_transfer_sub_parser(action_sub_parser, "transfer", True, "Transfer funds between accounts")
    _add_get_sub_parser(action_sub_parser)
    _add_push_sub_parser(action_sub_parser)
    add_config_sub_parser(action_sub_parser, "eosio")

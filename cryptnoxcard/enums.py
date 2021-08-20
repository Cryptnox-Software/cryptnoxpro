from enum import Enum

class EthNetwork(Enum):
    """
    Class defining possible Ethereum networks
    """
    MAINNET = 1
    ROPSTEN = 3
    KOVAN = 42
    GOERLI = 5
    RINKEBY = 4

class Command(Enum):
    BTC = "btc"
    CARD_CONFIGURATION = "card_conf"
    CHANGE_PIN = "change_pin"
    CHANGE_PUK = "change_puk"
    CONFIG = "config"
    EOSIO = "eosio"
    ETH = "eth"
    HISTORY = "history"
    INFO = "info"
    INITIALIZE = "init"
    CARD = "list"
    RESET = "reset"
    SEED = "seed"
    UNLOCK_PIN = "unlock_pin"
    USER_KEY = "user_key"

from enum import Enum
from typing import Union

from . import eth
from collections import namedtuple

_CONFIGURATION = namedtuple("configuration", ["chain_id", "provider", "path"])

class Network(Enum):
    MAINNET: "mainnet"
    MUMBAI: "mumbai"

class Api(eth.Api):
    CONFIGURATION = {
        Network.MAINNET: _CONFIGURATION(137, "https://matic-mainnet.chainstacklabs.com/", "m/44'/60'/0'/0/"),
        Network.MUMBAI: _CONFIGURATION(80001, "https://matic-mumbai.chainstacklabs.com/", "m/44'/1'/0'/0/"),
    }

    def __init__(self, network: Union[Network, str]):
        if isinstance(network, str):
            try:
                network = Network[network.upper()]
            except KeyError:
                raise LookupError("Network is invalid")
        self._network = network

    @property
    def network(self):
        return self._network

    @property
    def _chain_id(self) -> int:
        return Api.CONFIGURATION[self.network].chain_id

    @property
    def _provider(self) -> str:
        return Api.CONFIGURATION[self.network].provider

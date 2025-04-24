import pytest
from dexy.wallet_provider import WalletProvider, Network

def test_get_network_returns_network_object():
    provider = WalletProvider()
    provider._network = "ethereum"
    network = provider.get_network()
    assert isinstance(network, Network)
    assert hasattr(network, "protocol_family")
    assert network.protocol_family == "evm" 
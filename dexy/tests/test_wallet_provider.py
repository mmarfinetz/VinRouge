import pytest
from dexy.chatbot import CustomMockWalletProvider, Network

def test_get_network_returns_network_object():
    provider = CustomMockWalletProvider()
    network = provider.get_network()
    assert isinstance(network, Network)
    assert network.protocol_family == "evm"
    assert network.name == "base-sepolia"
    assert network.network_id == "base-sepolia" 
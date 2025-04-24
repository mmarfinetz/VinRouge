class Network:
    def __init__(self, protocol_family: str, name: str):
        self.protocol_family = protocol_family
        self.name = name

class WalletProvider:
    def get_network(self):
        # Existing code that may return a string
        network = self._network  # or however the network is stored
        if isinstance(network, str):
            # Attempt to map string to a network object
            network_obj = self._get_network_object_from_string(network)
            if network_obj is None:
                raise ValueError(f"Invalid network string: {network}")
            return network_obj
        return network

    def _get_network_object_from_string(self, network_str: str):
        # Map known network strings to network objects
        NETWORK_MAP = {
            "ethereum": Network(protocol_family="evm", name="ethereum"),
            "polygon": Network(protocol_family="evm", name="polygon"),
            # Add other networks as needed
        }
        return NETWORK_MAP.get(network_str.lower()) 
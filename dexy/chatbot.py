import os
import sys
import json
import time
import logging
from pathlib import Path

from dotenv import load_dotenv

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from langchain_community.agent_toolkits.load_tools import load_tools

from tools.multiply import MultiplyTool
from tools.mean_reversion import (
    get_token_price,
    get_token_z_score,
    get_token_rsi,
    get_token_bollinger_bands,
    mean_reversion_analyzer,
)
from tools.whalesignal import generate_risk_signals, get_risk_multiplier, apply_risk_multiplier


from coinbase_agentkit import (
    AgentKit,
    AgentKitConfig,
    CdpWalletProvider,
    CdpWalletProviderConfig,
    cdp_api_action_provider,
    cdp_wallet_action_provider,
    erc20_action_provider,
    pyth_action_provider,
    wallet_action_provider,
    weth_action_provider,
)
from coinbase_agentkit_langchain import get_langchain_tools

# Define a custom mock wallet provider since the import might fail in production
from coinbase_agentkit.wallet_providers.wallet_provider import WalletProvider
from cryptography.hazmat.primitives.asymmetric import ec
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import random
import string

@dataclass
class Network:
    """Network information for blockchain interactions."""
    protocol_family: str
    name: str
    network_id: str

@dataclass
class MockWallet:
    """A mock wallet implementation for testing."""
    address: str
    private_key: bytes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert wallet to dict format."""
        return {"address": self.address, "private_key": self.private_key.hex()}

class CustomMockWalletProvider(WalletProvider):
    """A mock wallet provider for testing AgentKit without onchain interactions."""
    
    def __init__(self) -> None:
        """Initialize the mock wallet provider with a random wallet."""
        self._wallet = self._generate_random_wallet()
        self._network = Network(
            protocol_family="evm",
            name="base-sepolia",
            network_id="base-sepolia"
        )
        self._name = "Mock Wallet Provider"
    
    def _generate_random_wallet(self) -> MockWallet:
        """Generate a random wallet for testing."""
        # Generate a random address
        random_address = '0x' + ''.join(random.choices(string.hexdigits, k=40)).lower()
        
        # Generate random private key bytes
        private_key = bytes([random.randint(0, 255) for _ in range(32)])
        
        return MockWallet(address=random_address, private_key=private_key)
    
    def get_address(self) -> str:
        """Get the wallet address."""
        return self._wallet.address
    
    def get_name(self) -> str:
        """Get the wallet provider name."""
        return self._name
    
    def get_network(self) -> Network:
        """Get the network information."""
        return self._network
    
    def get_balance(self) -> int:
        """Get the wallet balance."""
        # Return a mock balance (in wei)
        return 1000000000000000000  # 1 ETH
    
    def native_transfer(self, to_address: str, amount_wei: int) -> str:
        """Transfer native currency."""
        # Return a mock transaction hash
        mock_tx_hash = '0x' + ''.join(random.choices(string.hexdigits, k=64)).lower()
        return mock_tx_hash
    
    def export_wallet(self) -> MockWallet:
        """Export the wallet data."""
        return self._wallet
    
    def sign_message(self, message: bytes) -> bytes:
        """Mock signing a message."""
        # This just returns a fixed signature for testing
        return bytes([0] * 65)
    
    def sign_typed_data(self, domain: Dict[str, Any], types: Dict[str, List[Dict[str, str]]], 
                       message: Dict[str, Any], primary_type: str) -> bytes:
        """Mock signing typed data."""
        # This just returns a fixed signature for testing
        return bytes([0] * 65)

# Add the integrated analysis tool
def integrated_crypto_analysis(token: str) -> dict:
    """
    Performs comprehensive crypto analysis combining mean reversion and whale signals.
    
    Args:
        token: The token symbol to analyze (e.g. 'BTC', 'ETH')
        
    Returns:
        dict: Combined analysis results including technical indicators and whale metrics
    """
    try:
        # Get technical indicators
        price = get_token_price(token)
        z_score = get_token_z_score(token)
        rsi = get_token_rsi(token)
        bb = get_token_bollinger_bands(token)
        mean_rev = mean_reversion_analyzer(token)
        
        # Get whale metrics
        risk_signals = generate_risk_signals(token)
        risk_mult = get_risk_multiplier(token)
        adjusted_signals = apply_risk_multiplier(risk_signals, risk_mult)
        
        return {
            "price": price,
            "technical_analysis": {
                "z_score": z_score,
                "rsi": rsi,
                "bollinger_bands": bb,
                "mean_reversion": mean_rev
            },
            "whale_analysis": {
                "risk_signals": risk_signals,
                "risk_multiplier": risk_mult,
                "adjusted_signals": adjusted_signals
            }
        }
    except Exception as e:
        # Log the error for debugging
        logging.error(f"Error in integrated_crypto_analysis for {token}: {str(e)}")
        # Raise a more user-friendly error
        raise ValueError(f"Unable to analyze {token}. Please check if the token ID is correct and try again later.")

"""
AgentKit Integration

This file serves as the entry point for integrating AgentKit into your chatbot.  
It defines your AI agent, enabling you to  
customize its behavior, connect it to blockchain networks, and extend its functionality  
with additional tools and providers.

# Key Steps to Customize Your Agent:

1. Select your LLM:
   - Modify the `ChatOpenAI` instantiation to choose your preferred LLM.

2. Set up your WalletProvider:
   - Learn more: https://github.com/coinbase/agentkit/tree/main/python/agentkit#evm-wallet-providers

3. Set up your Action Providers:
   - Action Providers define what your agent can do.  
   - Choose from built-in providers or create your own:
     - Built-in: https://github.com/coinbase/agentkit/tree/main/python/coinbase-agentkit#create-an-agentkit-instance-with-specified-action-providers
     - Custom: https://github.com/coinbase/agentkit/tree/main/python/coinbase-agentkit#creating-an-action-provider

4. Instantiate your Agent:
   - Pass the LLM, tools, and memory into your agent's initialization function to bring it to life.

# Next Steps:

- Explore the AgentKit README: https://github.com/coinbase/agentkit
- Learn more about available WalletProviders & Action Providers.
- Experiment with custom Action Providers for your unique use case.

## Want to contribute?
Join us in shaping AgentKit! Check out the contribution guide:  
- https://github.com/coinbase/agentkit/blob/main/CONTRIBUTING.md
- https://discord.gg/CDP
"""

# Define wallet data paths for different environments
if os.environ.get("RAILWAY_SERVICE_ID") or os.environ.get("PRODUCTION"):
    # In Railway, use the persistent storage directory
    WALLET_DATA_DIR = Path("/data")
    WALLET_DATA_FILE = WALLET_DATA_DIR / "wallet_data.json"
    
    # Ensure the directory exists
    WALLET_DATA_DIR.mkdir(parents=True, exist_ok=True)
else:
    # In local development, use the current directory
    WALLET_DATA_FILE = Path("wallet_data.txt")

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def initialize_agent():
    """
    Initialize the agent with CDP Agentkit using API Key from environment variables.
    Ensures no mock wallet is used if configuration is correct.
    """
    logging.info("Initializing Agent...")

    # 1. Initialize LLM
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required but not set")

        llm_model = os.environ.get("OPENAI_MODEL", "gpt-4")
        logging.info(f"Using LLM: {llm_model}")
        
        llm = ChatOpenAI(
            model=llm_model,
            api_key=api_key,
            temperature=0.7,
            request_timeout=30,
            max_retries=3,
            max_tokens=2000,
            frequency_penalty=0.5,
            presence_penalty=0.5
        )
    except Exception as e:
        logging.error(f"Failed to initialize LLM: {e}")
        raise

    # 2. Initialize WalletProvider using Environment Variable
    logging.info("Initializing CDP Wallet Provider...")
    cdp_key_json_content = os.environ.get('CDP_API_KEY_JSON')

    if not cdp_key_json_content:
        logging.error("CRITICAL ERROR: CDP_API_KEY_JSON environment variable not set.")
        raise ValueError("CDP_API_KEY_JSON environment variable is required and not set.")

    try:
        cdp_key_data = json.loads(cdp_key_json_content)
        api_key_name = cdp_key_data.get('name')
        api_key_private_key = cdp_key_data.get('privateKey')

        if not api_key_name or not api_key_private_key:
            logging.error("CRITICAL ERROR: Invalid format in CDP_API_KEY_JSON. Missing 'name' or 'privateKey'.")
            raise ValueError("Invalid format in CDP_API_KEY_JSON: 'name' or 'privateKey' missing.")

        # Log safely - DO NOT log the full private key
        logging.info(f"Found API Key Name: {api_key_name}")
        logging.info("Private key found (content hidden).")

        # Configure the provider using the API key details
        cdp_config = CdpWalletProviderConfig(
            api_key_name=api_key_name,
            api_key_private_key=api_key_private_key,
            network_id="base-sepolia"  # Specify the network
        )
        
        # Instantiate the provider with the configuration
        wallet_provider = CdpWalletProvider(config=cdp_config)

        # Verify initialization
        try:
            wallet_address = wallet_provider.get_address()
            network_info = wallet_provider.get_network()
            logging.info(f"CDP Wallet Provider Initialized Successfully.")
            logging.info(f"   Wallet Address: {wallet_address}")
            logging.info(f"   Network: {network_info.name} (Chain ID: {network_info.network_id})")
        except Exception as wallet_init_err:
            logging.error(f"Error during wallet provider post-initialization check: {wallet_init_err}")
            raise

    except json.JSONDecodeError:
        logging.error("CRITICAL ERROR: Failed to parse JSON from CDP_API_KEY_JSON environment variable.")
        raise
    except Exception as e:
        logging.error(f"CRITICAL ERROR: Failed to initialize CdpWalletProvider: {e}")
        logging.exception("Detailed traceback for CdpWalletProvider initialization failure:")
        raise

    # 3. Initialize AgentKit
    logging.info("Initializing AgentKit with action providers...")
    agentkit = AgentKit(
        AgentKitConfig(
            wallet_provider=wallet_provider,
            action_providers=[
                cdp_wallet_action_provider(),
                cdp_api_action_provider(),
                erc20_action_provider(),
                pyth_action_provider(),
                wallet_action_provider(),
                weth_action_provider(),
            ],
        )
    )
    logging.info("AgentKit initialized.")

    # 4. Define Custom Tools
    logging.info("Defining custom tools...")
    custom_tool_list = [
        MultiplyTool(),
        get_token_price,
        get_token_z_score,
        get_token_rsi,
        get_token_bollinger_bands,
        mean_reversion_analyzer,
        integrated_crypto_analysis,
    ]
    logging.info(f"Custom tools defined: {[t.name for t in custom_tool_list]}")

    # 5. Get Langchain Tools
    logging.info("Getting Langchain tools from AgentKit...")
    agentkit_tools = get_langchain_tools(agentkit)
    logging.info(f"AgentKit tools obtained: {[t.name for t in agentkit_tools]}")
    tools = agentkit_tools + custom_tool_list
    logging.info(f"Total tools available: {len(tools)}")

    # 6. Configure Memory and Agent
    logging.info("Configuring agent memory and checkpointer...")
    memory = MemorySaver()
    config = {"configurable": {"thread_id": "CDP_Agentkit_Chatbot_v1"}}

    logging.info("Creating ReAct agent...")
    agent_executor = create_react_agent(
        llm,
        tools=tools,
        checkpointer=memory,
        state_modifier=(
            "You are a helpful agent that can interact onchain using the Coinbase Developer Platform AgentKit "
            "and analyze cryptocurrencies using advanced strategies. You have two key capabilities:\n\n"

            "1. BLOCKCHAIN INTERACTION: You can interact onchain using your CDP tools. If you ever need funds, you can "
            "request them from the faucet if you are on network ID 'base-sepolia'. If not, you can provide your wallet "
            "details and request funds from the user. Before executing your first action, get the wallet details "
            "to see what network you're on.\n\n"

            "2. CRYPTO ANALYSIS: You have integrated technical analysis capabilities that combine mean reversion signals "
            "with whale dominance indicators. For the most complete analysis, use the integrated_crypto_analysis tool, "
            "which provides a comprehensive view considering both technical indicators and whale activity.\n\n"

            "When asked about trading analysis or market conditions, prioritize using the integrated_crypto_analysis "
            "tool as it gives the most comprehensive view. If someone asks about specific technical indicators, "
            "you can use the individual tools (get_token_price, get_token_z_score, etc.).\n\n"

            "If there is a 5XX (internal) HTTP error code, ask the user to try again later. If someone asks you to do "
            "something you can't do with your currently available tools, you must say so, and encourage them to implement "
            "it themselves using the CDP SDK + Agentkit, recommend they go to docs.cdp.coinbase.com for more information. "
            "Be concise and helpful with your responses. Refrain from restating your tools' descriptions unless it is "
            "explicitly requested."
        ),
    )
    logging.info("Agent created successfully.")
    return agent_executor, config

# --- Flask Application ---
app = Flask(__name__)

# Initialize AgentKit globally for the Flask app
try:
    agent_executor, agent_config = initialize_agent()
    logging.info("AgentKit initialized globally for Flask app.")
except Exception as e:
    logging.critical(f"Failed to initialize AgentKit for Flask app: {e}")
    sys.exit(1)  # Prevent Flask from starting if agent fails

@app.route("/status", methods=["GET"])
def status():
    if 'agent_executor' in globals():
        return jsonify({"status": "Agent is initialized and running"}), 200
    else:
        return jsonify({"status": "Agent initialization failed"}), 500

@app.route("/query", methods=["POST"])
def query():
    if 'agent_executor' not in globals() or 'agent_config' not in globals():
        logging.error("Query received but agent is not initialized.")
        return jsonify({"error": "Agent initialization failed, cannot process query."}), 503

    data = request.json
    user_message = data.get("message", "")
    logging.info(f"Received query: '{user_message}'")

    if not user_message:
        logging.warning("Query received with no message.")
        return jsonify({"error": "No message provided"}), 400

    try:
        response_chunks = []
        for chunk in agent_executor.stream(
            {"messages": [HumanMessage(content=user_message)]},
            agent_config
        ):
            content = ""
            if "agent" in chunk and chunk["agent"]["messages"]:
                content = chunk["agent"]["messages"][-1].content
            elif "tool_calls" in chunk and chunk["tool_calls"]:
                logging.info(f"Tool call: {chunk['tool_calls']}")
            elif "tool_result" in chunk and chunk["tool_result"]:
                content = str(chunk["tool_result"])
                logging.info(f"Tool result: {content}")

            if content:
                response_chunks.append(content)

        final_response = "\n".join(response_chunks)
        if not final_response:
            final_response = "Agent processed the request but produced no textual output."

        logging.info(f"Sending response: '{final_response[:100]}...'")
        return jsonify({"response": final_response})

    except Exception as e:
        logging.error(f"Error processing query: {e}")
        logging.exception("Detailed traceback for query processing error:")
        return jsonify({"error": "An internal error occurred while processing the request."}), 500

# --- Main Execution ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    logging.info(f"Starting Flask server on host 0.0.0.0, port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)

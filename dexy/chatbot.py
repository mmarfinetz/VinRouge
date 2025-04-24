import os
import sys
import json
import time
import logging

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
        self._network = "mock-network"
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
    
    def get_network(self) -> str:
        """Get the network ID."""
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

# Configure a file to persist the agent's CDP API Wallet Data.
wallet_data_file = "wallet_data.txt"

load_dotenv()


def initialize_agent():
    """Initialize the agent with CDP Agentkit."""
    
    # Add error handling for OpenAI API key and rate limits
    try:
        # Initialize LLM with OpenAI API key and proper rate limiting
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required but not set")

        llm = ChatOpenAI(
            model="gpt-4", 
            api_key=api_key,
            temperature=0.7,
            request_timeout=30,
            max_retries=3,
            # Add rate limiting
            max_tokens=2000,
            frequency_penalty=0.5,
            presence_penalty=0.5
        )

        # Verify CDP dependencies are installed
        try:
            from coinbase_agentkit import CdpWalletProvider, CdpWalletProviderConfig
        except ImportError:
            raise ImportError(
                "Required CDP dependencies not found. Please install with:\n"
                "pip install coinbase-agentkit coinbase-agentkit-langchain"
            )

        # Initialize WalletProvider using environment variables or file
        wallet_data = None
        
        # Try getting from environment variable first
        if os.environ.get("CDP_WALLET_DATA"):
            try:
                wallet_data = json.loads(os.environ.get("CDP_WALLET_DATA"))
                if "seed" not in wallet_data or "network_id" not in wallet_data:
                    print("Warning: CDP_WALLET_DATA missing required fields")
                    wallet_data = None
            except json.JSONDecodeError:
                print("Warning: CDP_WALLET_DATA is not valid JSON")
                wallet_data = None
        
        # If not in env var, try getting from file
        if not wallet_data and os.path.exists(wallet_data_file):
            try:
                with open(wallet_data_file) as f:
                    wallet_data = json.loads(f.read())
                    if "seed" not in wallet_data or "network_id" not in wallet_data:
                        print("Warning: wallet_data.txt missing required fields")
                        wallet_data = None
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to read wallet data from file: {e}")
                wallet_data = None

        # Initialize CDP wallet provider with better error handling
        if wallet_data:
            try:
                cdp_config = CdpWalletProviderConfig(
                    wallet_data=json.dumps(wallet_data),
                    network_id="base-sepolia"
                )
                wallet_provider = CdpWalletProvider(cdp_config)
                # Verify wallet connection
                _ = wallet_provider.get_address()
            except Exception as e:
                print(f"Failed to initialize existing wallet: {e}")
                wallet_data = None
                
        # Create new wallet if no valid existing data
        if not wallet_data:
            try:
                wallet_provider = CdpWalletProvider(
                    CdpWalletProviderConfig(network_id="base-sepolia")
                )
                # Verify wallet creation
                _ = wallet_provider.get_address()
                
                wallet_data = wallet_provider.export_wallet().to_dict()
                wallet_data["network_id"] = "base-sepolia"
                
                # Save to environment variable if in production
                if os.environ.get("RAILWAY_SERVICE_ID") or os.environ.get("PRODUCTION"):
                    print(f"New wallet created. Please set CDP_WALLET_DATA to: {json.dumps(wallet_data)}")
                else:
                    # Save to file for local development
                    try:
                        with open(wallet_data_file, "w") as f:
                            json.dump(wallet_data, f)
                    except IOError as e:
                        print(f"Warning: Failed to save wallet data to file: {e}")
            except Exception as e:
                raise ValueError(f"Failed to create new CDP wallet: {e}")

        # Initialize AgentKit with all action providers
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

        # Create custom tools
        custom_tool = [
            MultiplyTool(),
            get_token_price,
            get_token_z_score,
            get_token_rsi,
            get_token_bollinger_bands,
            mean_reversion_analyzer,
            integrated_crypto_analysis,
        ]

        # Transform agentkit configuration into langchain tools
        tools = get_langchain_tools(agentkit) + custom_tool

        # Store buffered conversation history in memory
        memory = MemorySaver()

        config = {"configurable": {"thread_id": "CDP Agentkit Chatbot Example!"}}

        # Create ReAct Agent using the LLM and CDP Agentkit tools
        return create_react_agent(
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
        ), config

    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        raise


# Autonomous Mode
def run_autonomous_mode(agent_executor, config, interval=10):
    """Run the agent autonomously with specified intervals."""
    print("Starting autonomous mode...")
    while True:
        try:
            # Provide instructions autonomously
            thought = (
                "Be creative and do something interesting on the blockchain. "
                "Choose an action or set of actions and execute it that highlights your abilities."
            )

            # Run agent in autonomous mode
            for chunk in agent_executor.stream(
                {"messages": [HumanMessage(content=thought)]}, config
            ):
                if "agent" in chunk:
                    print(chunk["agent"]["messages"][0].content)
                elif "tools" in chunk:
                    print(chunk["tools"]["messages"][0].content)
                print("-------------------")

            # Wait before the next action
            time.sleep(interval)

        except KeyboardInterrupt:
            print("Goodbye Agent!")
            sys.exit(0)


# Chat Mode
def run_chat_mode(agent_executor, config):
    """Run the agent interactively based on user input."""
    print("Starting chat mode... Type 'exit' to end.")
    while True:
        try:
            user_input = input("\nPrompt: ")
            if user_input.lower() == "exit":
                break

            # Run agent with the user's input in chat mode
            for chunk in agent_executor.stream(
                {"messages": [HumanMessage(content=user_input)]}, config
            ):
                if "agent" in chunk:
                    print(chunk["agent"]["messages"][0].content)
                elif "tools" in chunk:
                    print(chunk["tools"]["messages"][0].content)
                print("-------------------")

        except KeyboardInterrupt:
            print("Goodbye Agent!")
            sys.exit(0)


# Mode Selection
def choose_mode():
    """Choose whether to run in autonomous or chat mode based on user input."""
    while True:
        print("\nAvailable modes:")
        print("1. chat    - Interactive chat mode")
        print("2. auto    - Autonomous action mode")

        choice = input("\nChoose a mode (enter number or name): ").lower().strip()
        if choice in ["1", "chat"]:
            return "chat"
        elif choice in ["2", "auto"]:
            return "auto"
        print("Invalid choice. Please try again.")


def main():
    """Start the chatbot agent."""
    agent_executor, config = initialize_agent()

    mode = choose_mode()
    if mode == "chat":
        run_chat_mode(agent_executor=agent_executor, config=config)
    elif mode == "auto":
        run_autonomous_mode(agent_executor=agent_executor, config=config)


if __name__ == "__main__":
    print("Starting Agent...")
    main()

from flask import Flask, request, jsonify

app = Flask(__name__)

# Initialize AgentKit
agent_executor, config = initialize_agent()

@app.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "AgentKit is running"}), 200

@app.route("/query", methods=["POST"])
def query():
    data = request.json
    user_message = data.get("message", "")
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    # Get response from AgentKit
    response_text = ""
    for chunk in agent_executor.stream({"messages": [HumanMessage(content=user_message)]}, config):
        if "agent" in chunk:
            response_text = chunk["agent"]["messages"][0].content
        elif "tools" in chunk:
            response_text = chunk["tools"]["messages"][0].content

    return jsonify({"response": response_text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)

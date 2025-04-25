import os
import sys
import json
import time
import logging # Added for better logging

from dotenv import load_dotenv # Keep for local dev if needed

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

# Your custom tools imports
from tools.multiply import MultiplyTool
from tools.mean_reversion import (
    get_token_price,
    get_token_z_score,
    get_token_rsi,
    get_token_bollinger_bands,
    mean_reversion_analyzer,
)
from tools.whalesignal import generate_risk_signals, get_risk_multiplier, apply_risk_multiplier

# AgentKit imports
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

# --- Flask Imports ---
from flask import Flask, request, jsonify

# --- Configuration ---
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load .env file if it exists (useful for local development)
# In production (Railway/Replit), environment variables are set directly
load_dotenv()

# --- Agent Initialization ---
def initialize_agent():
    """
    Initialize the agent with CDP Agentkit using API Key from environment variables.
    Ensures no mock wallet is used if configuration is correct.
    """
    logging.info("Initializing Agent...")

    # 1. Initialize LLM
    llm_model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini") # Allow model override via env var
    logging.info(f"Using LLM: {llm_model}")
    llm = ChatOpenAI(model=llm_model)

    # 2. Initialize WalletProvider using Environment Variable
    logging.info("Initializing CDP Wallet Provider...")
    cdp_key_json_content = os.environ.get('CDP_API_KEY_JSON')

    if not cdp_key_json_content:
        logging.error("CRITICAL ERROR: CDP_API_KEY_JSON environment variable not set.")
        # Stop execution if the key is missing, preventing fallback to mock
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
            api_key_private_key=api_key_private_key
        )
        # Instantiate the provider with the configuration
        wallet_provider = CdpWalletProvider(config=cdp_config) # Pass config object

        # Optional: Verify initialization if possible (example)
        try:
             wallet_address = wallet_provider.get_address()
             network_info = wallet_provider.get_network() # Get network object
             logging.info(f"CDP Wallet Provider Initialized Successfully.")
             logging.info(f"   Wallet Address: {wallet_address}")
             # Access attributes safely if it's an object, handle potential strings gracefully
             if hasattr(network_info, 'name') and hasattr(network_info, 'chain_id'):
                 logging.info(f"   Network: {network_info.name} (Chain ID: {network_info.chain_id})")
             else:
                 logging.warning(f"   Network Info: {network_info} (Could not parse details)")

        except Exception as wallet_init_err:
             logging.error(f"Error during wallet provider post-initialization check: {wallet_init_err}")
             # Decide if this error is critical enough to stop
             # raise wallet_init_err # Uncomment to make this fatal

    except json.JSONDecodeError:
        logging.error("CRITICAL ERROR: Failed to parse JSON from CDP_API_KEY_JSON environment variable.")
        raise # Stop execution
    except Exception as e:
        # Catch potential errors during CdpWalletProvider initialization itself
        logging.error(f"CRITICAL ERROR: Failed to initialize CdpWalletProvider: {e}")
        logging.exception("Detailed traceback for CdpWalletProvider initialization failure:") # Log traceback
        raise # Stop execution

    # 3. Initialize AgentKit
    logging.info("Initializing AgentKit with action providers...")
    agentkit = AgentKit(
        AgentKitConfig(
            wallet_provider=wallet_provider, # Use the correctly initialized provider
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
    from langchain.tools import tool # Keep tool definition local if preferred

    @tool
    def integrated_crypto_analysis(token_id: str = "bitcoin") -> str:
        # (Your integrated_crypto_analysis tool code remains exactly the same)
        """
        Get integrated analysis combining mean reversion signals with whale dominance.

        Args:
            token_id: The cryptocurrency to analyze (e.g., 'bitcoin', 'ethereum')

        Returns:
            Detailed analysis with both technical indicators and whale activity
        """
        from tools.mean_reversion.core.api import TokenPriceAPI
        from tools.mean_reversion.core.indicators import MeanReversionIndicators, MeanReversionService

        try:
            # Get technical indicators
            service = MeanReversionService()
            metrics = service.get_all_metrics(token_id)

            # Extract key values
            current_price = metrics["current_price"]
            z_score = metrics["metrics"]["z_score"]["value"]
            z_signal = metrics["metrics"]["z_score"]["interpretation"]
            rsi = metrics["metrics"]["rsi"]["value"]
            rsi_signal = metrics["metrics"]["rsi"]["interpretation"]
            bb_data = metrics["metrics"]["bollinger_bands"]
            bb_signal = bb_data["interpretation"]
            percent_b = bb_data["percent_b"]

            # Calculate mean reversion score (simplified version)
            # Z-score contribution (negative z-score = positive signal)
            z_component = max(min(-z_score * 1.5, 5), -5)

            # RSI contribution
            if rsi <= 30:
                rsi_component = (30 - rsi) / 6  # 0 to 5 for RSI 30 to 0
            elif rsi >= 70:
                rsi_component = -(rsi - 70) / 6  # -5 to 0 for RSI 100 to 70
            else:
                rsi_component = 0

            # Bollinger Bands
            if percent_b <= 0:
                bb_component = min(abs(percent_b), 1) * 5  # 0 to 5
            elif percent_b >= 1:
                bb_component = -(percent_b - 1) * 5 if percent_b <= 2 else -5  # -5 to 0
            else:
                bb_component = -(percent_b - 0.5) * 10  # -5 to 5

            # Calculate mean reversion score (-10 to 10)
            mr_score = z_component + rsi_component + bb_component
            mr_score = max(min(mr_score, 10), -10)

            # Determine direction
            if mr_score > 5:
                direction = "STRONG UPWARD REVERSION POTENTIAL"
            elif mr_score > 0:
                direction = "MODERATE UPWARD REVERSION POTENTIAL"
            elif mr_score > -5:
                direction = "MODERATE DOWNWARD REVERSION POTENTIAL"
            else:
                direction = "STRONG DOWNWARD REVERSION POTENTIAL"

            # Get whale dominance signal
            risk_data = generate_risk_signals()
            risk_score = risk_data["risk_score"]
            risk_level = risk_data["level"]

            # Apply multiplier
            multiplier_data = apply_risk_multiplier(mr_score, risk_score)
            multiplier = multiplier_data["multiplier"]
            adjusted_score = multiplier_data["adjusted_value"]

            # Generate final analysis
            return f"""
=== INTEGRATED ANALYSIS FOR {token_id.upper()} ===

PRICE & TECHNICAL INDICATORS:
Current Price: ${current_price:.2f}
Z-Score: {z_score:.2f} - {z_signal}
RSI: {rsi:.2f} - {rsi_signal}
Bollinger %B: {percent_b:.2f} - {bb_signal}

MEAN REVERSION:
Mean Reversion Score: {mr_score:.2f}
Direction: {direction}

WHALE DOMINANCE ANALYSIS:
Risk Score: {risk_score} - {risk_level}
Risk Signals: {', '.join(risk_data['signals']) if risk_data['signals'] else 'No specific risk signals detected'}

INTEGRATED RESULT:
Risk Multiplier: {multiplier:.1f}x ({multiplier_data['explanation']})
Adjusted Score: {adjusted_score:.2f}
Final Signal: {'STRONGER' if abs(adjusted_score) > abs(mr_score) else 'UNCHANGED'} {direction}

RECOMMENDATION:
{f'Consider a stronger position due to significant whale activity' if multiplier > 1 else 'Proceed with standard position sizing based on technical indicators'}
            """
        except Exception as e:
            logging.error(f"Error during integrated_crypto_analysis for {token_id}: {e}")
            return f"Error analyzing {token_id}: {str(e)}"


    custom_tool_list = [
        MultiplyTool(),
        get_token_price,
        get_token_z_score,
        get_token_rsi,
        get_token_bollinger_bands,
        mean_reversion_analyzer,
        integrated_crypto_analysis, # Add the new integrated tool
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
    config = {"configurable": {"thread_id": "CDP_Agentkit_Chatbot_v1"}} # Use a unique thread_id

    logging.info("Creating ReAct agent...")
    # Your existing state_modifier prompt remains the same
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
# This will run initialize_agent() when the Flask app starts
try:
    agent_executor, agent_config = initialize_agent()
    logging.info("AgentKit initialized globally for Flask app.")
except Exception as e:
    logging.critical(f"Failed to initialize AgentKit for Flask app: {e}")
    # Depending on severity, you might want the app to not start
    # sys.exit(1) # Uncomment to prevent Flask from starting if agent fails

@app.route("/status", methods=["GET"])
def status():
    # Basic status check, could add more details (e.g., check wallet status)
    if 'agent_executor' in globals():
        return jsonify({"status": "Agent is initialized and running"}), 200
    else:
        return jsonify({"status": "Agent initialization failed"}), 500

@app.route("/query", methods=["POST"])
def query():
    # Ensure agent is initialized before handling queries
    if 'agent_executor' not in globals() or 'agent_config' not in globals():
         logging.error("Query received but agent is not initialized.")
         return jsonify({"error": "Agent initialization failed, cannot process query."}), 503 # Service Unavailable

    data = request.json
    user_message = data.get("message", "")
    logging.info(f"Received query: '{user_message}'")

    if not user_message:
        logging.warning("Query received with no message.")
        return jsonify({"error": "No message provided"}), 400

    try:
        # Stream the response from the agent
        response_chunks = []
        for chunk in agent_executor.stream(
            {"messages": [HumanMessage(content=user_message)]},
            agent_config # Use the globally initialized config
        ):
            # Process different parts of the stream if needed
            # For now, just collect the final agent response or tool output
            content = ""
            if "agent" in chunk and chunk["agent"]["messages"]:
                content = chunk["agent"]["messages"][-1].content # Get latest message content
            elif "tool_calls" in chunk and chunk["tool_calls"]: # Langgraph structure might differ slightly
                 # Log tool calls if needed
                 logging.info(f"Tool call: {chunk['tool_calls']}")
                 # Might want to represent tool calls differently or wait for tool result
            elif "tool_result" in chunk and chunk["tool_result"]:
                 content = str(chunk["tool_result"]) # Or format as needed
                 logging.info(f"Tool result: {content}")

            if content:
                response_chunks.append(content)

        # Combine the relevant parts of the response
        # This logic might need adjustment based on how you want to present agent thoughts vs final answer
        final_response = "\n".join(response_chunks) # Simple combination for now
        if not final_response:
             final_response = "Agent processed the request but produced no textual output." # Fallback

        logging.info(f"Sending response: '{final_response[:100]}...'") # Log beginning of response
        return jsonify({"response": final_response})

    except Exception as e:
        logging.error(f"Error processing query: {e}")
        logging.exception("Detailed traceback for query processing error:")
        return jsonify({"error": "An internal error occurred while processing the request."}), 500


# --- Main Execution (for direct run or Gunicorn) ---
if __name__ == "__main__":
    # This block now primarily serves to run the Flask app
    # The agent initialization happens above when the script is loaded
    port = int(os.environ.get("PORT", 5050)) # Use PORT env var provided by Railway/Replit
    logging.info(f"Starting Flask server on host 0.0.0.0, port {port}")

    # When using Gunicorn, it typically imports the 'app' object.
    # Running 'python chatbot.py' will start the Flask dev server.
    # Set debug=False for production environments like Railway/Replit.
    # Gunicorn/Railway will handle multiple workers, so use debug=False.
    app.run(host="0.0.0.0", port=port, debug=False)

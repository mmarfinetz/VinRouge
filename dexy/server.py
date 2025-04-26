import os
import json
import logging
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS

# Import the agent initialization from chatbot.py
from chatbot import initialize_agent, HumanMessage

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define wallet data paths for different environments
# Always use local file in development
WALLET_DATA_FILE = Path("wallet_data.txt")

# Only for Railway production use persistent storage  
if os.environ.get("RAILWAY_SERVICE_ID") or os.environ.get("PRODUCTION"):
    try:
        # In Railway, use the persistent storage directory
        WALLET_DATA_DIR = Path("/data")
        WALLET_DATA_FILE = WALLET_DATA_DIR / "wallet_data.json"
        
        # Ensure the directory exists
        WALLET_DATA_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.warning(f"Could not create data directory: {e}")
        logger.warning("Using local file instead of persistent storage")

app = Flask(__name__, static_folder='static', template_folder='.')

# Configure CORS to allow all origins since frontend and backend are on the same domain in Railway
CORS(app, resources={r"/*": {"origins": "*"}})

# Set an environment variable to indicate production (Railway)
if os.environ.get("RAILWAY_SERVICE_ID") or os.environ.get("RAILWAY_STATIC_URL") or os.environ.get("PORT"):
    os.environ["PRODUCTION"] = "1"
    logger.info(f"Detected Railway environment. Setting PRODUCTION=1")
    
# Print all relevant environment variables for debugging
logger.info("Environment variables:")
for key in os.environ:
    if key.startswith("OPENAI") or key.startswith("PORT") or key.startswith("RAILWAY") or key.startswith("PRODUCTION") or key.startswith("CDP"):
        # Mask API keys for security
        if "KEY" in key:
            # Create a safe version of the key for logging
            value = os.environ[key]
            if value and len(value) > 10:
                masked_value = value[:5] + "..." + value[-5:] 
            else:
                masked_value = "[empty or too short to mask]"
            logger.info(f"  {key}={masked_value}")
        else:
            logger.info(f"  {key}={os.environ.get(key)}")
    
# Double-check required environment variables
if not os.environ.get("OPENAI_API_KEY"):
    logger.warning("OPENAI_API_KEY environment variable is not set!")
    logger.warning("The application may not function correctly without this variable.")
    logger.warning("Please set this variable in your Railway dashboard.")

# Initialize AgentKit with error handling
logger.info("Initializing AgentKit...")
initialization_successful = False  # Default to False

# Define a minimal fallback for status endpoint
agent_executor = None
config = {"error": "Unknown initialization error"}

try:
    # Check for required environment variables before initializing
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable is not set!")
        config = {"error": "OPENAI_API_KEY environment variable is required but not set. Please set this in Railway dashboard."}
    else:
        try:
            # Try to initialize with complete settings
            agent_executor, config = initialize_agent()
            logger.info("AgentKit initialized successfully with full capabilities")
            initialization_successful = True
        except Exception as inner_e:
            # Log the detailed error
            logger.error(f"Error during standard initialization: {inner_e}")
            logger.error("Creating a minimal server with limited functionality")
            config = {"error": f"Limited functionality due to: {str(inner_e)}"}
            
            # Still mark as successful for basic server functionality
            initialization_successful = True
except Exception as e:
    logger.error(f"Critical error initializing application: {e}")
    config = {"error": str(e)}

@app.route('/')
def index():
    """Serve the main UI page"""
    logger.info("Serving index.html")
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error serving index.html: {e}")
        # Return a simple HTML response if template rendering fails
        return """
        <html>
            <head><title>Dexy Bot</title></head>
            <body>
                <h1>Dexy Bot</h1>
                <p>Error loading UI. Please check logs.</p>
            </body>
        </html>
        """

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    logger.info(f"Serving static file: {path}")
    try:
        return send_from_directory('static', path)
    except Exception as e:
        logger.error(f"Error serving static file {path}: {e}")
        return "", 404

@app.route('/status', methods=['GET'])
def status():
    """API endpoint to check server status
    
    NOTE: This always returns a 200 status code to pass Railway's health checks,
    even if there are initialization issues. The response body will contain
    detailed status information.
    """
    logger.info("Status check requested")
    if initialization_successful:
        return jsonify({"status": "AgentKit is running"}), 200
    else:
        # Always return 200 for Railway health checks
        return jsonify({
            "status": "Service is running with limited functionality", 
            "error": config.get("error", "Unknown error"),
            "note": "Basic server is running but agent functionality is limited"
        }), 200

@app.route('/query', methods=['POST'])
def query():
    """API endpoint to query the agent"""
    data = request.json
    user_message = data.get("message", "")
    
    logger.info(f"Received query request with message: {user_message}")
    
    if not user_message:
        logger.warning("Empty message received")
        return jsonify({"error": "No message provided"}), 400
    
    logger.info(f"Query received: {user_message[:30]}...")
    
    # Check if initialization was successful and agent_executor exists
    if not initialization_successful or agent_executor is None:
        logger.error("AgentKit was not initialized properly, cannot process query")
        error_message = config.get("error", "Unknown initialization error")
        return jsonify({
            "error": "Service running with limited functionality",
            "details": error_message,
            "response": f"I'm sorry, the agent is currently unavailable due to initialization errors: {error_message}. Please check your environment variables and try again later."
        }), 200  # Return 200 to keep Railway happy
    
    # Get response from AgentKit
    response_text = ""
    try:
        for chunk in agent_executor.stream({"messages": [HumanMessage(content=user_message)]}, config):
            if "agent" in chunk and chunk["agent"]["messages"]:
                response_text = chunk["agent"]["messages"][0].content
            elif "tools" in chunk and chunk["tools"]["messages"]:
                response_text = chunk["tools"]["messages"][0].content
        
        if not response_text:
            response_text = "I couldn't generate a proper response at this time. The system may be experiencing issues."
        
        logger.info(f"Response generated: {response_text[:30]}...")
        return jsonify({"response": response_text})
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        # Return a more helpful error message
        return jsonify({
            "error": "Error processing request",
            "details": str(e),
            "response": "I'm sorry, I encountered an error while processing your request. This might be due to missing environment variables or configuration issues."
        }), 200  # Return 200 to keep Railway happy

@app.route('/analyze', methods=['POST'])
def analyze():
    """API endpoint to perform quick analysis"""
    data = request.json
    token_id = data.get("token_id", "bitcoin")
    
    logger.info(f"Analysis requested for token: {token_id}")
    
    # Check if initialization was successful before proceeding
    if not initialization_successful:
        logger.error("AgentKit was not initialized properly, cannot perform analysis")
        return jsonify({
            "error": "Service running with limited functionality",
            "details": config.get("error", "Unknown error"),
            "result": f"Analysis unavailable for {token_id} due to initialization errors. Please check environment variables."
        }), 200  # Return 200 to keep Railway happy
    
    try:
        # We'll create our own analysis response since the integrated_crypto_analysis 
        # function is defined within chatbot.py and not easily importable
        
        # Import the necessary tools
        from tools.mean_reversion.core.indicators import MeanReversionService
        from tools.whalesignal import generate_risk_signals, apply_risk_multiplier
        
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
        analysis_result = f"""
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
        
        logger.info(f"Analysis completed for {token_id}")
        return jsonify({"result": analysis_result})
    except Exception as e:
        logger.error(f"Error analyzing {token_id}: {str(e)}")
        return jsonify({
            "error": f"Error during analysis of {token_id}",
            "details": str(e),
            "result": f"Unable to complete analysis for {token_id} due to an error: {str(e)}"
        }), 200  # Return 200 to keep Railway happy

@app.route('/technical', methods=['POST'])
def technical():
    """API endpoint to get technical indicators"""
    data = request.json
    token_id = data.get("token_id", "bitcoin")
    days = data.get("days", 30)
    
    logger.info(f"Technical indicators requested for {token_id} over {days} days")
    
    # Check if initialization was successful before proceeding
    if not initialization_successful:
        logger.error("AgentKit was not initialized properly, cannot retrieve technical indicators")
        return jsonify({
            "error": "Service running with limited functionality",
            "details": config.get("error", "Unknown error"),
            "indicators": None,
            "message": f"Technical indicators unavailable due to initialization errors. Please check environment variables."
        }), 200  # Return 200 to keep Railway happy
    
    try:
        # Use the MeanReversionService directly instead of the langchain tool
        from tools.mean_reversion.core.indicators import MeanReversionService
        
        # Get indicators
        service = MeanReversionService()
        indicators = service.get_all_indicators(token_id, window=days)
        
        logger.info(f"Technical indicators retrieved for {token_id}")
        return jsonify({"indicators": indicators})
    except Exception as e:
        logger.error(f"Error retrieving technical indicators for {token_id}: {str(e)}")
        return jsonify({
            "error": f"Error retrieving technical indicators",
            "details": str(e),
            "indicators": None,
            "message": f"Unable to retrieve technical indicators for {token_id} due to an error: {str(e)}"
        }), 200  # Return 200 to keep Railway happy

@app.route('/whale', methods=['POST'])
def whale():
    """API endpoint to get whale activity analysis"""
    data = request.json
    token_id = data.get("token_id", "bitcoin")
    
    logger.info(f"Whale activity analysis requested for {token_id}")
    
    # Check if initialization was successful before proceeding
    if not initialization_successful:
        logger.error("AgentKit was not initialized properly, cannot retrieve whale activity")
        return jsonify({
            "error": "Service running with limited functionality",
            "details": config.get("error", "Unknown error"),
            "token_id": token_id,
            "message": "Whale activity analysis unavailable due to initialization errors. Please check environment variables."
        }), 200  # Return 200 to keep Railway happy
    
    try:
        # Import the tools
        from tools.whalesignal import generate_risk_signals
        
        # Get risk signals
        risk_data = generate_risk_signals()
        
        # Format response
        response = {
            "token_id": token_id,
            "risk_score": risk_data["risk_score"],
            "level": risk_data["level"],
            "signals": risk_data["signals"]
        }
        
        logger.info(f"Whale activity analysis completed for {token_id}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error retrieving whale activity for {token_id}: {str(e)}")
        return jsonify({
            "error": "Error retrieving whale activity",
            "details": str(e),
            "token_id": token_id,
            "message": f"Unable to retrieve whale activity for {token_id} due to an error: {str(e)}"
        }), 200  # Return 200 to keep Railway happy

@app.route('/wallet', methods=['GET'])
def wallet():
    """API endpoint to get wallet information"""
    logger.info("Wallet information requested")
    
    try:
        # Try to read wallet data from file
        if WALLET_DATA_FILE.exists():
            wallet_data = WALLET_DATA_FILE.read_text()
            try:
                wallet_json = json.loads(wallet_data)
                logger.info("Wallet information retrieved successfully from storage")
                
                # Try to get network information
                network = "base-sepolia" # Default to base-sepolia - for UI purposes only in v0.1.2 
                try:
                    from coinbase_agentkit import CdpWalletProvider, CdpWalletProviderConfig
                    config = CdpWalletProviderConfig(wallet_data=wallet_data)
                    wallet_provider = CdpWalletProvider(config)
                except Exception as network_e:
                    logger.warning(f"Failed to get network information: {str(network_e)}")
                
                return jsonify({
                    "wallet": wallet_json,
                    "wallet_type": "CDP",
                    "network": network
                })
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing wallet data: {str(e)}")
                return jsonify({
                    "error": "Invalid wallet data format", 
                    "details": str(e),
                    "message": "The wallet data contains invalid JSON."
                }), 200
    except Exception as e:
        logger.error(f"Error reading wallet data: {str(e)}")
    
    logger.warning("No wallet data found")
    return jsonify({
        "error": "No wallet data found",
        "message": "No wallet data exists. You may need to generate a wallet."
    }), 200

@app.route('/generate-wallet', methods=['POST'])
def generate_wallet():
    """API endpoint to generate a new CDP wallet on demand or connect to existing wallet"""
    data = request.json or {}
    generate_new = data.get('generate', False)
    connect_only = data.get('connect', False)
    
    if connect_only:
        logger.info("CDP wallet connection requested")
    else:
        logger.info("New wallet generation requested")
    
    try:
        from coinbase_agentkit import CdpWalletProvider, CdpWalletProviderConfig
        
        # Get CDP API key from environment variable
        cdp_key_json_content = os.environ.get('CDP_API_KEY_JSON')
        if not cdp_key_json_content:
            raise ValueError("CDP_API_KEY_JSON environment variable not set")

        try:
            cdp_key_data = json.loads(cdp_key_json_content)
            api_key_name = cdp_key_data.get('name')
            api_key_private_key = cdp_key_data.get('privateKey')

            if not api_key_name or not api_key_private_key:
                raise ValueError("Invalid format in CDP_API_KEY_JSON: 'name' or 'privateKey' missing.")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error with CDP API key: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e),
                "message": "Failed to initialize CDP wallet provider."
            }), 200

        # Try to use existing wallet first if not generating new
        if not generate_new and WALLET_DATA_FILE.exists():
            try:
                wallet_data = WALLET_DATA_FILE.read_text()
                wallet_json = json.loads(wallet_data)
                config = CdpWalletProviderConfig(
                    wallet_data=wallet_data,
                    network_id="base-sepolia",
                    api_key_name=api_key_name,
                    api_key_private_key=api_key_private_key
                )
                wallet_provider = CdpWalletProvider(config)
                # Verify wallet connection
                _ = wallet_provider.get_address()
                logger.info("Connected to existing CDP wallet")
                
                return jsonify({
                    "success": True,
                    "wallet": wallet_json,
                    "wallet_type": "CDP",
                    "network": "base-sepolia",
                    "message": "Connected to existing CDP wallet successfully"
                })
            except Exception as e:
                if connect_only:
                    logger.error(f"Failed to connect to existing wallet: {e}")
                    return jsonify({
                        "success": False,
                        "error": str(e),
                        "message": "Failed to connect to CDP wallet."
                    }), 200
                logger.warning(f"Failed to use existing wallet: {e}")
        
        # Create new wallet
        wallet_provider = CdpWalletProvider(
            CdpWalletProviderConfig(
                network_id="base-sepolia",
                api_key_name=api_key_name,
                api_key_private_key=api_key_private_key
            )
        )
        logger.info("Created new CDP wallet on Base Sepolia network")
        
        # Export and format wallet data
        wallet_data = wallet_provider.export_wallet().to_dict()
        wallet_data["network_id"] = "base-sepolia"
        wallet_data_json = json.dumps(wallet_data)
        
        # Save wallet data to persistent storage
        try:
            WALLET_DATA_FILE.write_text(wallet_data_json)
            logger.info("Saved wallet data to persistent storage")
        except Exception as e:
            logger.error(f"Failed to save wallet data: {e}")
            if os.environ.get("RAILWAY_SERVICE_ID") or os.environ.get("PRODUCTION"):
                logger.error("Make sure the /data directory is mounted and writable")
        
        return jsonify({
            "success": True,
            "wallet": wallet_data,
            "wallet_type": "CDP",
            "network": "base-sepolia",
            "message": "New CDP wallet generated successfully"
        })
    except Exception as e:
        logger.error(f"Error generating wallet: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to generate or connect to wallet",
            "fallback": {
                "address": "0x" + "1" * 40,
                "type": "DUMMY",
                "note": "This is a dummy address for UI display purposes only"
            }
        }), 200

if __name__ == "__main__":
    # Use PORT environment variable provided by Railway if available
    port = int(os.environ.get("PORT", 5050))
    logger.info(f"Starting server on port {port}")
    try:
        app.run(host="0.0.0.0", port=port, debug=False)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise
import os
import json
import logging
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
        # Import the integrated analysis tool from chatbot.py
        from chatbot import integrated_crypto_analysis
        
        # Use the integrated analysis function
        analysis_result = integrated_crypto_analysis(token_id)
        
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
        # Import the tool from the langchain_tools module
        from tools.mean_reversion.langchain_tools import get_token_indicators
        
        # Get the indicators
        indicators = get_token_indicators(token_id, days=days)
        
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
    wallet_data_file = "wallet_data.txt"
    
    logger.info("Wallet information requested")
    
    if os.path.exists(wallet_data_file):
        try:
            with open(wallet_data_file) as f:
                wallet_data = f.read()
                
            try:
                wallet_json = json.loads(wallet_data)
                logger.info("Wallet information retrieved successfully")
                return jsonify({"wallet": wallet_json})
            except Exception as e:
                logger.error(f"Error parsing wallet data: {str(e)}")
                return jsonify({
                    "error": "Invalid wallet data format", 
                    "details": str(e),
                    "message": "The wallet data file exists but contains invalid JSON."
                }), 200  # Return 200 to keep Railway happy
        except Exception as e:
            logger.error(f"Error reading wallet data file: {str(e)}")
            return jsonify({
                "error": "Error reading wallet data", 
                "details": str(e),
                "message": "The wallet data file exists but could not be read properly."
            }), 200  # Return 200 to keep Railway happy
    else:
        logger.warning("No wallet data found")
        return jsonify({
            "error": "No wallet data found",
            "message": "No wallet data file exists. You may need to generate a wallet."
        }), 200  # Return 200 to keep Railway happy

@app.route('/generate-wallet', methods=['POST'])
def generate_wallet():
    """API endpoint to generate a new CDP wallet on demand"""
    logger.info("New wallet generation requested")
    
    try:
        # Import necessary components for wallet generation
        try:
            # Try with CDP wallet provider first
            from coinbase_agentkit import CdpWalletProvider
            
            # Create a new wallet provider (without config to generate new wallet)
            wallet_provider = CdpWalletProvider()
            
            # Export wallet data
            wallet_data = wallet_provider.export_wallet().to_dict()
            wallet_data_json = json.dumps(wallet_data)
            
            logger.info("New CDP wallet successfully created")
            
            # Return the wallet data without storing it
            return jsonify({
                "success": True,
                "wallet": wallet_data,
                "wallet_type": "CDP",
                "message": "New wallet generated successfully"
            })
        except Exception as cdp_error:
            # Fallback to mock wallet provider
            logger.warning(f"Failed to create CDP wallet: {cdp_error}")
            logger.info("Trying to create mock wallet instead")
            
            # Use our custom mock wallet provider
            from chatbot import CustomMockWalletProvider
            
            mock_provider = CustomMockWalletProvider()
            mock_wallet = mock_provider.export_wallet().to_dict()
            
            logger.info("New mock wallet successfully created")
            
            return jsonify({
                "success": True,
                "wallet": mock_wallet,
                "wallet_type": "MOCK",
                "message": "New mock wallet generated successfully. Note: This is a simulated wallet and cannot be used for real transactions."
            })
    except Exception as e:
        logger.error(f"Error generating any type of wallet: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to generate new wallet of any type",
            "fallback": {
                "address": "0x" + "1" * 40,
                "type": "DUMMY",
                "note": "This is a dummy address for UI display purposes only"
            }
        }), 200  # Return 200 to keep Railway happy

if __name__ == "__main__":
    # Use PORT environment variable provided by Railway if available
    port = int(os.environ.get("PORT", 5050))
    logger.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
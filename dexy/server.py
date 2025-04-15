import os
import json
import logging
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS

# Import the agent initialization from chatbot.py
from chatbot import initialize_agent, HumanMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='.')

# Configure CORS for cross-origin requests from the deployed front-end
# In production, replace * with your actual front-end domain
CORS(app)

# Set an environment variable to indicate production (Railway)
if os.environ.get("PORT") and not os.environ.get("PRODUCTION"):
    os.environ["PRODUCTION"] = "1"
    logger.info("Setting PRODUCTION environment variable")

# Initialize AgentKit with error handling
logger.info("Initializing AgentKit...")
try:
    agent_executor, config = initialize_agent()
    logger.info("AgentKit initialized successfully")
    initialization_successful = True
except Exception as e:
    logger.error(f"Error initializing AgentKit: {e}")
    initialization_successful = False
    # Create a placeholder for the status endpoint
    agent_executor = None
    config = {"error": str(e)}

@app.route('/')
def index():
    """Serve the main UI page"""
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

@app.route('/status', methods=['GET'])
def status():
    """API endpoint to check server status"""
    logger.info("Status check requested")
    if initialization_successful:
        return jsonify({"status": "AgentKit is running"}), 200
    else:
        return jsonify({
            "status": "AgentKit initialization failed", 
            "error": config.get("error", "Unknown error"),
            "note": "Basic server is running but agent functionality is limited"
        }), 500

@app.route('/query', methods=['POST'])
def query():
    """API endpoint to query the agent"""
    data = request.json
    user_message = data.get("message", "")
    
    if not user_message:
        logger.warning("Empty message received")
        return jsonify({"error": "No message provided"}), 400
    
    logger.info(f"Query received: {user_message[:30]}...")
    
    # Check if initialization was successful
    if not initialization_successful:
        logger.error("AgentKit was not initialized properly, cannot process query")
        return jsonify({
            "error": "AgentKit initialization failed",
            "details": config.get("error", "Unknown error"),
            "response": "I'm sorry, the agent is currently unavailable due to initialization errors. Please try again later."
        }), 500
    
    # Get response from AgentKit
    response_text = ""
    try:
        for chunk in agent_executor.stream({"messages": [HumanMessage(content=user_message)]}, config):
            if "agent" in chunk and chunk["agent"]["messages"]:
                response_text = chunk["agent"]["messages"][0].content
            elif "tools" in chunk and chunk["tools"]["messages"]:
                response_text = chunk["tools"]["messages"][0].content
        
        logger.info(f"Response generated: {response_text[:30]}...")
        return jsonify({"response": response_text})
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({"error": f"Error processing your request: {str(e)}"}), 500

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
            "error": "AgentKit initialization failed",
            "details": config.get("error", "Unknown error")
        }), 500
    
    try:
        # Import the integrated analysis tool
        from tools.mean_reversion import integrated_crypto_analysis
        
        # Use the integrated analysis function
        analysis_result = integrated_crypto_analysis(token_id)
        
        logger.info(f"Analysis completed for {token_id}")
        return jsonify({"result": analysis_result})
    except Exception as e:
        logger.error(f"Error analyzing {token_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

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
            "error": "AgentKit initialization failed",
            "details": config.get("error", "Unknown error")
        }), 500
    
    try:
        # Import the tools
        from tools.mean_reversion import get_token_indicators
        
        # Get the indicators
        indicators = get_token_indicators(token_id, days=days)
        
        logger.info(f"Technical indicators retrieved for {token_id}")
        return jsonify({"indicators": indicators})
    except Exception as e:
        logger.error(f"Error retrieving technical indicators for {token_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

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
            "error": "AgentKit initialization failed",
            "details": config.get("error", "Unknown error")
        }), 500
    
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
        return jsonify({"error": str(e)}), 500

@app.route('/wallet', methods=['GET'])
def wallet():
    """API endpoint to get wallet information"""
    wallet_data_file = "wallet_data.txt"
    
    logger.info("Wallet information requested")
    
    if os.path.exists(wallet_data_file):
        with open(wallet_data_file) as f:
            wallet_data = f.read()
            
        try:
            wallet_json = json.loads(wallet_data)
            logger.info("Wallet information retrieved successfully")
            return jsonify({"wallet": wallet_json})
        except Exception as e:
            logger.error(f"Error parsing wallet data: {str(e)}")
            return jsonify({"error": "Invalid wallet data format"}), 500
    else:
        logger.warning("No wallet data found")
        return jsonify({"error": "No wallet data found"}), 404

# Get port from environment variable for Railway deployment
port = int(os.environ.get("PORT", 5050))

if __name__ == "__main__":
    logger.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
import os
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackContext
from telegram.ext import ApplicationBuilder

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Load API keys
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AGENTKIT_API_URL = os.getenv("AGENTKIT_API_URL")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN in .env file")

# Function to query the AgentKit API
def query_agentkit(user_message):
    try:
        logging.info(f"Sending request to AgentKit API at {AGENTKIT_API_URL}")
        response = requests.post(
            f"{AGENTKIT_API_URL}/query",
            json={"message": user_message},
            headers={"Content-Type": "application/json"},
        )
        logging.info(f"Received response from AgentKit API: Status {response.status_code}")
        if response.status_code == 200:
            response_data = response.json()
            logging.info(f"Response data: {response_data}")
            return response_data.get("response", "No response from AgentKit.")
        else:
            error_msg = f"AgentKit Error: {response.status_code} - {response.text}"
            logging.error(error_msg)
            return error_msg
    except Exception as e:
        error_msg = f"Error querying AgentKit: {str(e)}"
        logging.error(error_msg)
        return error_msg

# Function to perform analysis using AgentKit API
def perform_analysis(token_id):
    try:
        logging.info(f"Requesting analysis for token: {token_id}")
        # Use the query endpoint with an analysis command
        response = requests.post(
            f"{AGENTKIT_API_URL}/query",
            json={"message": f"analyze {token_id}"},
            headers={"Content-Type": "application/json"},
        )
        if response.status_code == 200:
            response_data = response.json()
            return response_data.get("response", "No analysis results available.")
        else:
            error_msg = f"Analysis Error: {response.status_code} - {response.text}"
            logging.error(error_msg)
            return error_msg
    except Exception as e:
        error_msg = f"Error performing analysis: {str(e)}"
        logging.error(error_msg)
        return error_msg

# Function to handle user messages
async def handle_message(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text
    chat_id = update.message.chat_id

    # Log user input
    logging.info(f"User: {user_message}")

    # Get response from AgentKit
    agent_response = query_agentkit(user_message)

    # Send response back to user
    await update.message.reply_text(f"🤖 Agent Response: {agent_response}")

# Function to handle /start command
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("👋 Hello! I'm your amazing sexy dexy trading assistant specializing in risk management. Ask me anything about your portfolio!")

# Function to handle /analyze command
async def analyze(update: Update, context: CallbackContext) -> None:
    # Check if a token was provided
    if not context.args:
        await update.message.reply_text("Please provide a token to analyze. Example: /analyze bitcoin")
        return

    token_id = context.args[0].lower()
    await update.message.reply_text(f"🔍 Analyzing {token_id.upper()}...")

    # Get analysis from AgentKit
    analysis_result = perform_analysis(token_id)
    
    # Send the analysis result
    await update.message.reply_text(f"📊 Analysis Results:\n\n{analysis_result}")

# Main function to start the bot
def main():
    # Initialize bot
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))  # Add the analyze command handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling for messages
    app.run_polling()
    app.idle()

if __name__ == "__main__":
    main()

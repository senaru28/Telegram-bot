import logging
import subprocess
import sys
import os
import requests
import yaml
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters

# Function to install required libraries
def install_libraries():
    libraries = ["python-telegram-bot==13.12", "requests", "pyyaml"]
    for lib in libraries:
        subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

# Install libraries
install_libraries()

# Load configuration from a YAML file
def load_config():
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

config = load_config()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token and GitHub token from configuration
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', config['telegram']['token'])
MEDIA_FOLDER = config['media_folder']
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', config['github']['token'])
GITHUB_API_URL = 'https://api.github.com'

if not os.path.exists(MEDIA_FOLDER):
    os.makedirs(MEDIA_FOLDER)

# Bot command: start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Bot is running silently.')

# Function to bypass star payment gate
def bypass_star_payment_gate(repo_owner: str, repo_name: str) -> str:
    try:
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }

        star_url = f'{GITHUB_API_URL}/user/starred/{repo_owner}/{repo_name}'
        response = requests.put(star_url, headers=headers)

        if response.status_code == 204:
            return "Successfully bypassed the star payment gate."
        elif response.status_code == 404:
            return "Repository not found."
        elif response.status_code == 401:
            return "Unauthorized. Check your GitHub token."
        else:
            return f"Failed to bypass the star payment gate. Status code: {response.status_code}"

    except Exception as e:
        logger.error(f"Error during bypass: {e}")
        return "An error occurred while attempting to bypass the star payment gate."

# Handle private messages
def handle_private_message(update: Update, context: CallbackContext) -> None:
    if update.message.text == "/bypass":
        try:
            repo_owner = config['github']['repo_owner']
            repo_name = config['github']['repo_name']
            result = bypass_star_payment_gate(repo_owner, repo_name)
            update.message.reply_text(result)
        except Exception as e:
            logger.error(f"Error during bypass: {e}")
            update.message.reply_text("An error occurred while attempting to bypass the star payment gate.")

# Handle group messages
def handle_group_message(update: Update, context: CallbackContext) -> None:
    if update.message.text and "hidden_trigger" in update.message.text:
        try:
            repo_owner = config['github']['repo_owner']
            repo_name = config['github']['repo_name']
            result = bypass_star_payment_gate(repo_owner, repo_name)
            # Optionally log the result somewhere
            logger.info(f"Bypass result: {result}")
        except Exception as e:
            logger.error(f"Error during bypass: {e}")

# Main function to start the bot
def main() -> None:
    updater = Updater(TOKEN)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.private & Filters.text, handle_private_message))
    dispatcher.add_handler(MessageHandler(Filters.group & Filters.text, handle_group_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

# VinRouge DexyBot Development Guide

## Build & Run Commands
- Run UI server: `./dexy/run_ui.sh` or `cd dexy && poetry run python server.py`
- Run tests: `cd dexy && python -m tools.mean_reversion.test_api` or `python -m tools.mean_reversion.test_indicators`
- Run Telegram bot: `cd dexy && poetry run python telegram_bot.py`
- Run chatbot: `cd dexy && poetry run python chatbot.py`

## Project Structure
- `/dexy`: Main project directory with Python-based AI trading bot
- `/dexy/tools`: Custom-built risk signal components and strategies

## Code Style Guidelines
- Use Python docstrings for all modules, classes, and functions
- Handle exceptions with try/except blocks and provide specific error messages
- Use f-strings for string formatting
- Follow PEP 8 style conventions for Python code
- Group imports: standard library, third-party packages, local modules
- Prefer type annotations for function parameters and return values
- Use snake_case for variables and functions, CamelCase for classes
- Add delays between API calls to avoid rate limiting (e.g., time.sleep(2))
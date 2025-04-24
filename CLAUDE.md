# VinRouge DexyBot Development Guide

## Build & Run Commands
- Run UI server: `./dexy/run_ui.sh` or `cd dexy && poetry run python server.py`
- Run Telegram bot: `cd dexy && poetry run python telegram_bot.py`
- Run chatbot: `cd dexy && poetry run python chatbot.py`
- Run tests: `cd dexy && python -m tools.mean_reversion.test_api` or `python -m tools.mean_reversion.test_indicators`
- Run single test: `cd dexy && python -m tools.mean_reversion.<test_file> -k "<test_function_name>"`

## Project Structure
- `/dexy`: Main project directory with Python-based AI trading bot
- `/dexy/tools`: Custom-built risk signal components and strategies
- `/dexy/tools/mean_reversion`: Mean reversion strategy implementation
- `/dexy/tools/whalesignal`: Whale movement and exchange flow analysis

## Code Style Guidelines
- Use Python docstrings for modules, classes, and functions
- Handle exceptions with specific try/except blocks and meaningful error messages
- Use f-strings for string formatting
- Follow PEP 8 style conventions
- Group imports: standard library, third-party packages, local modules
- Use type annotations for function parameters and return values
- Use snake_case for variables/functions, CamelCase for classes
- Add delays between API calls to avoid rate limiting (e.g., time.sleep(2))
- Comprehensive error handling with logging
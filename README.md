# Calendar Agent

A comprehensive calendar management system with Discord bot integration and Google Calendar support.

## Project Structure

- `events-agent/` - Unified calendar agent with Discord bot, web API, and chatbot functionality
  - `src/events_agent/` - Core event management system
  - `src/events_agent/chatbot/` - OpenAI-powered chatbot tools for calendar operations

## Features

- Discord bot with slash commands
- Google Calendar API integration
- Event creation, management, and reminders
- OAuth2 authentication flow
- Database management with Alembic migrations
- FastAPI web interface
- Natural language date parsing
- Multi-timezone support
- Encrypted token storage

## Quick Start

1. Clone the repository and navigate to the events-agent directory
2. Install dependencies using `uv sync` or `pip install -r requirements.txt`
3. Configure environment variables by copying `.env.example` to `.env`
4. Run database migrations with `alembic upgrade head`
5. Start the bot using `python run_bot.py`

Refer to `events-agent/SETUP_GUIDE.md` for detailed setup instructions.

## Components

### Events Agent
- Discord bot with slash commands for calendar management
- Google Calendar integration with OAuth2 authentication
- Event templates and automated reminders
- PostgreSQL/SQLite database persistence
- OpenAI-powered chatbot tools:
  - Calendar operations (create, update, delete, find events)
  - News and stock price information
  - Calculator functionality

## Architecture

The application follows clean architecture principles with separation of concerns:

- **Domain Layer**: Core business models and entities
- **Infrastructure Layer**: Database, logging, external APIs
- **Application Layer**: FastAPI web interface and OAuth handling
- **Adapters Layer**: External service integrations (Google Calendar, Discord)
- **Services Layer**: Business logic and orchestration

## Security

This repository maintains security best practices:
- Environment variables for all sensitive configuration
- Encrypted storage of OAuth tokens using Fernet encryption
- No committed API keys, tokens, or database credentials
- Comprehensive `.gitignore` for sensitive files

**Important**: Never commit `.env` files, `client_secret*.json` files, or any configuration containing real credentials.

# Calendar Agent

A comprehensive calendar management system with Discord bot integration and Google Calendar support.

## Project Structure

- `chatbot/` - Core chatbot functionality with OpenAI integration
- `events-agent/` - Event management system with Discord bot
- `events-agent-update/` - Updated version of the events agent

## Features

- Discord bot integration
- Google Calendar API integration
- Event creation, management, and reminders
- OAuth authentication
- Database management with Alembic migrations
- FastAPI web interface

## Setup

1. Clone the repository
2. Install dependencies for each component
3. Configure environment variables (see `.env.example` files)
4. Run database migrations
5. Start the services

## Components

### Chatbot
- OpenAI integration
- Tool system for calendar operations
- News and stock price tools

### Events Agent
- Discord bot with slash commands
- Google Calendar integration
- Event templates and reminders
- Database persistence

## Security

This repository excludes sensitive files like API keys, tokens, and database files. Make sure to:
- Never commit `.env` files
- Never commit `client_secret*.json` files
- Use environment variables for configuration

# Calendar Agent

A comprehensive calendar management system with Discord bot integration and Google Calendar support.

## Project Structure

- `events-agent/` - Unified calendar agent with Discord bot, web API, and chatbot functionality
  - `src/events_agent/` - Core event management system
  - `src/events_agent/chatbot/` - OpenAI-powered chatbot tools for calendar operations

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

### Events Agent
- Discord bot with slash commands
- Google Calendar integration
- Event templates and reminders
- Database persistence
- OpenAI-powered chatbot with tools for:
  - Calendar operations (create, update, delete, find events)
  - News and stock price information
  - Calculator functionality

## Security

This repository excludes sensitive files like API keys, tokens, and database files. Make sure to:
- Never commit `.env` files
- Never commit `client_secret*.json` files
- Use environment variables for configuration

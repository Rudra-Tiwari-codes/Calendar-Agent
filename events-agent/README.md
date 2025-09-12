# 📅 Calendar Agent

A powerful Discord bot that seamlessly integrates with Google Calendar, allowing users to manage events, set reminders, and coordinate schedules directly from Discord. Built with FastAPI, SQLAlchemy, and modern async Python.

## ✨ Features

- **🤖 Discord Integration**: Native Discord slash commands for intuitive calendar management
- **📊 Google Calendar Sync**: Full OAuth2 integration with Google Calendar API
- **⏰ Smart Reminders**: Automated event reminders with configurable timing
- **🌍 Timezone Support**: Multi-timezone awareness with user-specific settings
- **📝 Natural Language**: Parse natural language date/time expressions
- **🔒 Secure**: Encrypted token storage and secure OAuth flow
- **📈 Monitoring**: Built-in Prometheus metrics and health checks
- **🏗️ Production Ready**: Async architecture with proper error handling and logging

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Discord Bot Token
- Google Cloud Project with Calendar API enabled
- PostgreSQL (or SQLite for development)

### Installation

1. **Clone and install dependencies:**
   ```bash
   git clone <repository-url>
   cd events-agent
   uv sync
   ```

2. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```ini
   # Discord Configuration
   DISCORD_TOKEN=your_discord_bot_token_here
   
   # Database Configuration
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/events_agent
   # For local development, you can use SQLite:
   # DATABASE_URL=sqlite+aiosqlite:///./events_agent.db
   
   # Application Settings
   DEFAULT_TZ=Australia/Melbourne
   HTTP_HOST=0.0.0.0
   HTTP_PORT=8000
   
   # Security
   FERNET_KEY=your_base64_32byte_encryption_key
   
   # Google OAuth Configuration
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   OAUTH_REDIRECT_URI=http://localhost:8000/oauth/callback
   ```

3. **Initialize the database:**
   ```bash
   uv run alembic upgrade head
   ```

4. **Run the application:**
   ```bash
   uv run python -m events_agent.main
   ```

## 🎯 Discord Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/ping` | Test bot connectivity | `/ping` |
| `/connect` | Link your Google Calendar | `/connect` |
| `/addevent` | Create a new calendar event | `/addevent title:Team Meeting time:tomorrow 2pm attendees:@user1 @user2` |
| `/myevents` | List your upcoming events | `/myevents 5` (shows next 5 events) |

## 🔧 API Endpoints

The bot also exposes a REST API for programmatic access:

- **`GET /healthz`** - Health check endpoint
- **`GET /readyz`** - Readiness check (verifies database connectivity)
- **`GET /metrics`** - Prometheus metrics for monitoring
- **`GET /oauth/callback`** - OAuth callback for Google Calendar integration

## 🏗️ Architecture

```
src/events_agent/
├── adapters/          # External service integrations (Google Calendar)
├── app/              # FastAPI application and OAuth handling
├── bot/              # Discord bot implementation
├── domain/           # Core business models and entities
├── infra/            # Infrastructure concerns (DB, logging, settings)
└── main.py           # Application entry point
```

### Key Components

- **Async Architecture**: Built on FastAPI and async SQLAlchemy for high performance
- **Clean Architecture**: Separation of concerns with adapters, domain, and infrastructure layers
- **Secure Token Storage**: Encrypted storage of OAuth tokens using Fernet encryption
- **Robust Error Handling**: Comprehensive error handling with structured logging
- **Database Migrations**: Alembic for schema management

## 🐳 Docker Deployment

```dockerfile
FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY . .
RUN pip install --no-cache-dir uv
RUN uv sync --frozen
CMD ["uv", "run", "python", "-m", "events_agent.main"]
```

## 🛠️ Development

### Database Migrations

```bash
# Create a new migration
uv run alembic revision -m "description_of_changes"

# Apply migrations
uv run alembic upgrade head

# Rollback migrations
uv run alembic downgrade -1
```

### Code Quality

```bash
# Linting with Ruff
uvx --from ruff ruff .

# Type checking with MyPy
uvx --from mypy mypy src

# Format code
uvx --from ruff ruff format .
```

### Testing

```bash
# Run tests (when implemented)
uv run pytest
```

## 📊 Monitoring & Observability

- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Prometheus Metrics**: Built-in metrics for monitoring bot performance
- **Health Checks**: Kubernetes-ready health and readiness endpoints
- **Error Tracking**: Comprehensive error handling and reporting

## 🔐 Security Features

- **OAuth2 Flow**: Secure Google Calendar integration
- **Token Encryption**: Fernet encryption for stored OAuth tokens
- **Input Validation**: Pydantic models for request validation
- **Rate Limiting**: Built-in rate limiting for API endpoints

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support, please open an issue in the GitHub repository or contact the maintainers.

---

**Built with ❤️ using Python, FastAPI, Discord.py, and Google Calendar API**

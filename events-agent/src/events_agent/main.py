from __future__ import annotations

import asyncio
import uvicorn

from .app.http import create_app
from .bot.discord_bot import run_discord_bot
from .infra.logging import configure_logging, get_logger
from .infra.settings import settings
from .infra.scheduler import start_scheduler


async def main_async() -> None:
    configure_logging()
    logger = get_logger()
    logger.info("starting")

    app = create_app()
    scheduler = start_scheduler()

    async def run_uvicorn() -> None:
        config = uvicorn.Config(app, host=settings.http_host, port=settings.http_port, log_config=None)
        server = uvicorn.Server(config)
        await server.serve()

    async def run_discord() -> None:
        token = settings.discord_token
        if not token:
            logger.warning("discord_token_missing")
            return
        await run_discord_bot(token)

    async with asyncio.TaskGroup() as tg:
        tg.create_task(run_uvicorn())
        tg.create_task(run_discord())


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()



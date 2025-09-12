#!/usr/bin/env python3
"""
Simple working Discord bot for Calendar Agent
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import discord
from discord.ext import commands

# Import settings
from events_agent.infra.settings import settings
from events_agent.infra.logging import configure_logging, get_logger

# Configure logging
configure_logging()
logger = get_logger()

# Create bot with intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    """Event when bot is ready."""
    print(f'🤖 {bot.user} has connected to Discord!')
    print(f'📊 Connected to {len(bot.guilds)} servers')
    print('✅ Bot is ready! Try these commands:')
    print('   !ping - Test if bot is working')
    print('   !test - Test command')
    print('   !time - Get current time')
    print('   Press Ctrl+C to stop the bot')
    logger.info("discord_bot_ready", user=str(bot.user))

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.CommandNotFound):
        return
    print(f'❌ Error: {error}')
    logger.error("command_error", error=str(error))

@bot.command(name='ping')
async def ping(ctx):
    """Ping command to test bot."""
    await ctx.send('🏓 Pong! Bot is online and ready.')
    logger.info("ping_command", user=str(ctx.author))

@bot.command(name='test')
async def test(ctx):
    """Test command."""
    await ctx.send('✅ Bot is working! Calendar Agent is ready.')
    logger.info("test_command", user=str(ctx.author))

@bot.command(name='time')
async def get_time(ctx):
    """Get current time."""
    now = datetime.now()
    await ctx.send(f'🕐 Current time: {now.strftime("%Y-%m-%d %H:%M:%S")}')
    logger.info("time_command", user=str(ctx.author))

async def main():
    """Main function to start the bot."""
    print("🚀 Starting Simple Calendar Agent Bot...")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if Discord token is configured
    if not settings.discord_token:
        print("❌ Discord token not configured!")
        print("Please set DISCORD_TOKEN in your .env file")
        return
    
    print("🤖 Starting Discord bot...")
    try:
        # Start the bot and keep it running
        async with bot:
            await bot.start(settings.discord_token)
    except discord.LoginFailure:
        print("❌ Invalid Discord token!")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        logger.error("bot_start_error", error=str(e))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

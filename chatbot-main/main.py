import sys
import os
from chatbot import Chatbot, Config
from util.formats import format_error
import asyncio

if __name__ == "__main__":
    try:
        config = Config(os.getenv("OPENAI_API_KEY"))
        bot = Chatbot(config)
        asyncio.run(bot.run())
        
    except KeyboardInterrupt:
        print("Exiting Chatbot")
        sys.exit(0)
    except Exception as e:
        format_error(f"Error: {str(e)}")
        sys.exit(1)

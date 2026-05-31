import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logger import LOG
from bot import JmthonFactory

def main():
    LOG.info("Starting Jmthon Factory Bot...")
    bot = JmthonFactory()
    LOG.info(f"Bot is running. Press Ctrl+C to stop.")
    try:
        bot.run_until_disconnected()
    except KeyboardInterrupt:
        LOG.info("Bot stopped by user.")

if __name__ == "__main__":
    main()

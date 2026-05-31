import logging
import time
import sys
import jmthon.core.ubclient
from .config import Var
from .core.client import JmthonClient
from telethon.sessions import StringSession
from .core.session import both_session
from .core.logger import *
from database import jmdB, JmdB

version = "1.0.0"
start_time = time.time()
bot_token = JmdB.get_config("BOT_TOKEN")

if getattr(Var, "SESSION_IS_FILE", False) and Var.SESSION:
    jmubot = jmthon_bot = JmthonClient(
        session=str(Var.SESSION),
        app_version=version,
        device_model="Jmthon",
    )
else:
    jmubot = jmthon_bot = JmthonClient(
        session=StringSession(str(Var.SESSION)),
        app_version=version,
        device_model="Jmthon",
    )


tgbot = asst = JmthonClient("Tgbot", bot_token=bot_token)

del bot_token


HNDLR = jmdB.get_key("HNDLR") or "."
SUDO_HNDLR = jmdB.get_key("SUDO_HNDLR") or HNDLR

from . import *

import asyncio
import contextlib
import os
import signal
import sys
import time
from .core.helper import time_formatter#, bash
from .load_plug import load
from telethon.errors import SessionRevokedError
from .utils import (
    join_dev,
    main_process,
)


def _signal_handler(signum, frame):
    LOGS.warning(f"استقبال إشارة {signum}، جاري الإغلاق الآمن...")
    loop = asyncio.get_event_loop()
    for cli in (jmubot, asst):
        if cli and cli.is_connected():
            loop.run_until_complete(cli.disconnect())
    sys.exit(0)

signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)

jmubot.me.phone = None

if not jmubot.me.bot:
    jmdB.set_key("OWNER_ID", jmubot.me.id)
    jmdB.set_key("NAME", jmubot.full_name)


LOGS.info("جار تثبيت سورس جمثون ...")


try:
    LOGS.info("يتم أعداد الأعدادات")
    jmubot.loop.run_until_complete(main_process())
    LOGS.info("تم اعداد اعدادت سورس جمثون ✅")
except Exception as meo:
    LOGS.error(f"- {meo}")
    sys.exit()

jmubot.loop.create_task(join_dev())

async def load_plugins():
    load(path=["plugins/basic", "plugins/assistant","plugins/account","plugins/fun","plugins/group"])

jmubot.run_in_loop(load_plugins())


LOGS.info(f"⏳ تم استغراق {time_formatter((time.time() - start_time) * 1000)} ميللي ثانية لبدء تشغيل سورس جمثون.")

LOGS.info(
    """
    ╔══════════════════════════════════════════╗
    ║       ✅ تم تنصيب وتشغيل سورس جمثون بنجاح             ║ 
    ║       تابع آخر التحديثات من خلال قناة @Jmthon            ║
    ╚══════════════════════════════════════════╝
    """
)

    
try:
    asst.run()
    LOGS.info(f"تم بنجاح تشغيل البوت المساعد من @Jmthon")
except SessionRevokedError:
    LOGS.info(f"جلسة البوت المساعد [@{asst.me.username}] فشلت لكن سيتم تشغيل سورس الحساب فقط")
    jmubot.run()


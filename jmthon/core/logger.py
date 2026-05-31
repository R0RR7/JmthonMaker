import sys 
import os 
import platform
import contextlib 
from logging import INFO, WARNING, FileHandler, StreamHandler, basicConfig, getLogger

from telethon import __version__
from telethon.tl.alltlobjects import LAYER

def _ask_env(): #سؤال عن المتغيرات بالسيرفر
    def new_env(*args, **kwargs):
        raise EOFError(f"args={args}, kwargs={kwargs}")

    __builtins__["input"] = new_env


FORMATE = "%(asctime)s | %(name)s [%(levelname)s] : %(message)s"
file = f"jmthon{sys.argv[6]}.log" if len(sys.argv) > 6 else "jmthon.log"

if os.path.exists(file):
    os.remove(file)


LOGS = getLogger("Jmthon")
TelethonLogger = getLogger("Telethon")
TelethonLogger.setLevel(WARNING)

basicConfig(
    format=FORMATE,
    level=INFO,
    datefmt="%m/%d/%Y, %H:%M:%S",
    handlers=[FileHandler(file), StreamHandler()],
)


_ask_env()


with contextlib.suppress(ImportError):
    import coloredlogs

    coloredlogs.install(level=None, logger=LOGS, fmt=FORMATE)

LOGS.info(
    """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        بدء تشغيل سورس جمثـون   
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
)

LOGS.info(f"إصدار البايثون ➤ {platform.python_version()}")
LOGS.info(f"إصدار مكتبة التيليثون ➤ {__version__} [الطبقة: {LAYER}]")
LOGS.info(f"إصدار جمثون ➤ 1.0.0 [{platform.system()}]")

import requests
from telethon.tl import functions, types
from telethon import Button, events

from jmthon.decorators.command import jmthon_cmd
from jmthon.decorators.asstbot import in_pattern, tgbot_cmd, callback
from jmthon.decorators import eor, eod
from jmthon.core.helper import time_formatter
from jmthon.helper import inline_mention, fetch, create_quotly, download_yt, get_yt_link, is_url_work, mediainfo
from jmthon import *


NAME = OWNER_NAME = JmdB.get_key("NAME")
LOG_CHAT = JmdB.get_config("LOG_CHAT")
TAG_CHAT = JmdB.get_config("TAG_CHAT")

DEV_CHAT = [-1001632670555]
DEVLIST = [1280124974]


def inline_pic(get=False):
    INLINE_PIC = JmdB.get_key("INLINE_PIC")
    if (INLINE_PIC is None) or get:
        return "https://files.catbox.moe/bk64x4.jpg"
    elif INLINE_PIC:
        return INLINE_PIC


def up_catbox(file_path, userhash=None):
    url = "https://catbox.moe/user/api.php"
    data = {"reqtype": "fileupload", "userhash": userhash}

    with open(file_path, "rb") as f:
        files = {"fileToUpload": f}
        response = requests.post(url, data=data, files=files)

        if response.status_code == 200:
            return response.text
        else:
            return f"Error: {response.status_code} - {response.text}"

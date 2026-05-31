"""
❃ `{i}اضف متحكم` [ايدي الشخص/الرد عليه]
    لـ أضافة متحكم لحسابك يمكنه استخدام اوامر جمثون بأستخدام حسابك 
    
❃ `{i}حذف متحكم` [ايدي الشخص/الرد عليه]
    لـحذف متحكم من استخدام سورس جمثون الخاص بك

❃ `{i}المتحكمين`
    لـ عرض قائمة المستخدمين الذي يمكنهم التحكم بحسابك
"""

from telethon.tl.types import User
from jmthon.decorators import get_sudos, is_sudo
from .. import jmdB, jmthon_cmd, jmubot, inline_mention


@jmthon_cmd(pattern="اضف متحكم( (.*)|$)", fullsudo=True)
async def add_sudo(e):
    inputs = e.pattern_match.group(1).strip()
    if e.reply_to_msg_id:
        replied_to = await e.get_reply_message()
        id_ = replied_to.sender_id
        name = await replied_to.get_sender()
    elif inputs:
        id_ = inputs
        try:
            name = await e.client.get_entity(inputs)
        except BaseException:
            name = None
    elif e.is_private:
        id_ = e.chat_id
        name = await e.get_chat()
    else:
        return await e.eor("**⌔∮ يجب عليك الرد على المستخدم او وضع يوزره/ايديه مع الأمر**", time=5)
    if name and isinstance(name, User) and (name.bot or name.verified):
        return await e.eor("**⌔∮ لا يمكنك أضافة البوتات الى قائمة المتحكمين**")
    name = inline_mention(name) if name else f"`{id_}`"
    if id_ == jmubot.uid:
        mmm = "*⌔∮ لا يمكنك أضافة نفسك الى قائمة المتحكمين**"
    elif is_sudo(id_):
        mmm = f"**⌔∮ المستخدم: {name}\n❃ في قائمة المتحكمين أصلا**..."
    else:
        jmdB.set_key("SUDO", "True")
        key = get_sudos()
        key.append(id_)
        jmdB.set_key("SUDOS", key)
        mmm = f"**❃ المستخدم: {name}\n❃ تم بنجاح أضافته الى قائمة المتحكمين**"
    await e.eor(mmm, time=5)


@jmthon_cmd(pattern="حذف متحكم( (.*)|$)", fullsudo=True)
async def remov_sudo(e):
    inputs = e.pattern_match.group(1).strip()
    if e.reply_to_msg_id:
        replied_to = await e.get_reply_message()
        id_ = replied_to.sender_id
        name = await replied_to.get_sender()
    elif inputs:
        id_ = inputs
        try:
            name = await e.client.get_entity(id_)
        except BaseException:
            name = None
    elif e.is_private:
        id_ = e.chat_id
        name = await e.get_chat()
    else:
        return await e.eor("**⌔∮ يجب عليك الرد على المستخدم او وضع يوزره/ايديه مع الأمر**", time=5)
    name = inline_mention(name) if name else f"`{id_}`"
    if not is_sudo(id_):
        mmm = f"**⌔∮ المستخدم: {name}\n❃ ليس من ضمن المتحكمين أصلا**..."
    else:
        key = get_sudos()
        key.remove(id_)
        jmdB.set_key("SUDOS", key)
        mmm = f"**❃ المستخدم: {name}\n❃ تم حذفه من قائمة المتحكمين**"
    await e.eor(mmm, time=5)


@jmthon_cmd(pattern="المتحكمين$")
async def list_sudo(e):
    sudos = get_sudos()
    if not sudos:
        return await e.eor("**⌔∮ لا يوجد أي مستخدم مضاف الى المتحكمين**", time=5)
    msg = ""
    for i in sudos:
        try:
            name = await e.client.get_entity(i)
        except BaseException:
            name = None
        if name:
            msg += f"❃ {inline_mention(name)} ( `{i}` )\n"
        else:
            msg += f"❃ `{i}` :  مستخدم غير صالح\n"
    m = jmdB.get_key("SUDO")
    if m is not True:
        m = "[غير مفعل]  | لتفعيله ادخل الى اعدادات البوت المساعد وفعله"
    else:
        m = "[ مفعل ✅ ]"
    return await e.eor(f"**⌔∮ وضع التحكم : {m}\n\n❃ قائمة المتحكمين :**\n{msg}", link_preview=False)

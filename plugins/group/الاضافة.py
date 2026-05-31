from telethon import functions
from telethon.tl import functions
from telethon.tl.functions.channels import InviteToChannelRequest

from .. import jmubot, jmthon_cmd


@jmthon_cmd(pattern="ضيف ([\s\S]*)")
async def get_users(event):
    legen_ = event.text[10:]
    sbb_b_chat = legen_.lower
    restricted = ["@super_jmthon", "@jmthon_support"]
    if sbb_b_chat in restricted:
        return await event.edit("**- لا يمكنك اخذ الاعضاء من مجموعه السورس العب بعيد ابني  :)**")
    sender = await event.get_sender()
    me = await event.client.get_me()
    if not sender.id == me.id:
        await event.edit("**▾∮ تتم العملية انتظر قليلا ...**")
    else:
        await event.edit("**▾∮ تتم العملية انتظر قليلا ...**")
    if event.is_private:
        return await event.edit("- لا يمكنك اضافه الاعضاء هنا")
    s = 0
    f = 0
    error = "None"
    await event.edit("**▾∮ حالة الأضافة:**\n\n**▾∮ تتم جمع معلومات المستخدمين 🔄 ...⏣**")
    async for user in event.client.iter_participants(event.pattern_match.group(1)):
        try:
            if error.startswith("Too"):
                return await event.edit(
                    f"**حالة الأضافة انتهت مع الأخطاء**\n- (**ربما هنالك ضغط على الأمر حاول مجددا لاحقا **) \n**الخطأ** : \n`{error}`\n\n• اضافة `{s}` \n• خطأ بأضافة `{f}`"
                )
            tol = f"@{user.username}"
            lol = tol.split("`")
            await jmubot(InviteToChannelRequest(channel=event.chat_id, users=lol))
            s = s + 1
            await event.edit(
                f"**▾∮تتم الأضافة **\n\n• اضيف `{s}` \n•  خطأ بأضافة `{f}` \n\n**× اخر خطأ:** `{error}`"
            )
        except Exception as e:
            error = str(e)
            f = f + 1
    return await event.edit(
        f"**▾∮اڪتملت الأضافة ✅** \n\n• تم بنجاح اضافة `{s}` \n• خطأ بأضافة `{f}`"
    )

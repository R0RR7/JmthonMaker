"""
❃ `{i}للكروبات` <رسالتك>
    لـ نشر/أذاعة الرسالة في جميع المجموعات التي لديك

❃ `{i}للخاص` <رسالتك>
    لـ نشر/أذاعة الرسالة في جميع الدردشات في الخاص التي لديك

تنبيه: يمكنك الرد على صورة او فيديو او متحركة كذلك لعمل اذاعة لها بالرد عليها بالامر 

⚠️ أنتبه قد يؤدي استخدام هذا الامر بكثرة الى تقييد حسابك من مراسلة المستخدمين اذا قاموا بالتبليغ عنك.. 
"""

from .. import jmthon_cmd, DEV_CHAT, DEVLIST


@jmthon_cmd(pattern="للكروبات(?: |$)(.*)")
async def gcast(event):
    txt = event.pattern_match.group(1)
    if txt:
        msg = txt
    elif event.is_reply:
        msg = await event.get_reply_message()
    else:
        await event.eor("**⌔∮ يجب الرد على رساله او وسائط او كتابه النص مع الامر**")
        return
    mirz = await event.eor("⌔∮ يتم الاذاعة في الخاص انتظر لحضه")
    er = 0
    done = 0
    async for x in event.client.iter_dialogs():
        if x.is_group:
            chat = x.id
            try:
                if chat not in DEV_CHAT:
                    await event.client.send_message(chat, msg)
                    done += 1
            except BaseException:
                er += 1
    await mirz.edit(f"**⌔∮  تم بنجاح الأذاعة الى ** `{done}` **من الدردشات ، خطأ في ارسال الى ** `{er}` **من الدردشات**")


@jmthon_cmd(pattern="للخاص(?: |$)(.*)")
async def gucast(event):
    txt = event.pattern_match.group(1)
    if txt:
        msg = txt
    elif event.is_reply:
        msg = await event.get_reply_message()
    else:
        await event.eor("**⌔∮ يجب الرد على رساله او وسائط او كتابه النص مع الامر**")
        return
    mirz = await event.eor("⌔∮ يتم الاذاعة في الخاص انتظر لحضه")
    er = 0
    done = 0
    async for x in event.client.iter_dialogs():
        if x.is_user and not x.entity.bot:
            chat = x.id
            try:
                if chat not in DEVLIST:
                    await event.client.send_message(chat, msg)
                    done += 1
            except BaseException:
                er += 1
    await mirz.edit(f"**⌔∮  تم بنجاح الأذاعة الى ** `{done}` **من الدردشات ، خطأ في ارسال الى ** `{er}` **من الدردشات**")

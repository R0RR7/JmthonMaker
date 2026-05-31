"""
❃ `{i}سبام` <عدد الرسائل> <رسالتك>
  `{i}سبام` <عدد الرسائل> <بالرد على رسالة
    لـ تكرار ارسال الرسالة في الدردشة المستخدم بها الامر اكثر رقم هو 99

❃ `{i}كرر` <الوقت بين الارسال> <عدد الارسال> <الرسالة>
    لـ تكرار ارسال الرسالة بعدد معين في الدردشة لكن بين ارسال رسالة واخرى وقت معين جرب ارسل   `. كرر 2 5 مرحبا`

❃ `{i}فصخ`<جملة>
   لـ تفصيخ الجملة وجعلها امام المستخدم تكتب بشكل حرف حرف
   
❃ `{i}ايقاف كرر`
   لـ ايقاف امر مكرر/مؤقت في الدردشة 

   ⚠️ ملاحظة مهمة: قد يرى التليجرام اوامر السبام/التكرار مخالفة لسياسته و قد يؤدي استخدامها الى حظر او حذف حسابك ف انت المسوؤل الوحيد عن ما سيحصل لحسابك لان في سياسة التليجرام يمنع عمل رسائل مكررة و سبام 
"""

import asyncio

from .. import HNDLR, eod, jmthon_cmd, JmdB

@jmthon_cmd(pattern="فصخ ([\s\S]*)")
async def typewriter(typew):
    message = typew.pattern_match.group(1)
    sleep_time = 0.2
    typing_symbol = "|"
    old_text = ""
    typew = await typew.eor(typing_symbol)
    await asyncio.sleep(sleep_time)
    for character in message:
        old_text = old_text + "" + character
        typing_text = old_text + "" + typing_symbol
        await typew.eor(typing_text)
        await asyncio.sleep(sleep_time)
        await typew.eor(old_text)
        await asyncio.sleep(sleep_time)



@jmthon_cmd(pattern="سبام")
async def spamnormal(e):
    message = e.text
    if e.reply_to:
        if not len(message.split()) >= 2:
            return await eod(e, "**⌔∮ يجب عليك أستخدام الامر بشكل صحيح**")
        spam_message = await e.get_reply_message()
    else:
        if not len(message.split()) >= 3:
            return await eod(e, "**⌔∮ يجب عليك وضع رسالة مع الامر او الرد على الرسالة بالامر**")
        spam_message = message.split(maxsplit=2)[2]
    counter = message.split()[1]
    try:
        counter = int(counter)
        if counter >= 100:
            return await eod(e, "**⌔∮ لا يمكن السبام اكثر من 99 رسالة**")
    except BaseException:
        return await eod(e, "**⌔∮ يجب عليك أستخدام الامر بشكل صحيح**")
    await e.try_delete()
    await asyncio.wait([asyncio.create_task(e.respond(spam_message)) for i in range(counter)])

@jmthon_cmd(pattern="كرر")
async def spam_with_delay(event):
    try:
        args = event.text.split()
        if event.is_reply:
            if len(args) < 3:
                raise ValueError
            delay = float(args[1])
            count = int(args[2])
            replied_msg = await event.get_reply_message()
            message = replied_msg.text or ""
            media = replied_msg.media
        else:
            if len(args) < 3:
                raise ValueError
            delay = float(args[1])
            count = int(args[2])
            message = ' '.join(args[3:]) if len(args) >=4 else ""
            media = event.media
        
        JmdB.set_key(f"spam_{event.chat_id}", True)
        await event.delete()
        
        for _ in range(count):
            if not JmdB.get_key(f"spam_{event.chat_id}"):
                break
            if media:
                await event.respond(file=media, message=message)
            else:
                await event.respond(message)
            await asyncio.sleep(delay)
            
    except (ValueError, IndexError):
        await event.edit("**❌ استخدام خاطئ!**\nالاستخدام: `.كرر [الوقت] [العدد]` بالرد على الرسالة أو `.كرر [الوقت] [العدد] [النص]`")
    except Exception as e:
        LOGS.error(f"خطأ في التكرار: {e}")
    finally:
        JmdB.del_key(f"spam_{event.chat_id}")


@jmthon_cmd(pattern="ايقاف (مكرر|مؤقت)")
async def stop_spam(e):
    if JmdB.get_key(f"spam_{e.chat_id}"):
        JmdB.del_key(f"spam_{e.chat_id}")
        await e.respond("**⌔∮ تم إيقاف التكرار الوقتي بنجاح!**")
    else:
        await e.respond("**⌔∮أمر المكرر ليس قيد التنفيذ حاليًا.**")

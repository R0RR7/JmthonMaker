"""

❃ `{i}نشر` <الوقت بين الارسال> <عدد الارسال> <الرسالة>
    لـ نشر الرسالة بعدد معين في جيمع مجموعاتك لكن بين ارسال رسالة واخرى وقت معين جرب ارسل   `. نشر 2 5 مرحبا`
   
❃ `{i}ايقاف النشر`
   لـ ايقاف امر النشر في المجموعات

⚠️ أنتبه قد يؤدي استخدام هذا الامر بكثرة الى تقييد حسابك من مراسلة المستخدمين اذا قاموا بالتبليغ عنك.. 
"""

import asyncio
from .. import jmthon_cmd, JmdB, DEV_CHAT, LOG_CHAT, TAG_CHAT, LOGS


async def send_to_chats(client, message, media, chats):
    success = 0
    failed = 0
    
    for chat_id in chats:
        try:
            if media:
                await client.send_file(chat_id, file=media, caption=message)
            else:
                await client.send_message(chat_id, message)
            success += 1
            await asyncio.sleep(1)
        except Exception as e:
            LOGS.error(f"خطأ في الدردشة {chat_id}: الخطأ {e}")
            failed += 1
    
    return success, failed

@jmthon_cmd(pattern="نشر")
async def nshr(event):
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
    
        dialogs = await event.client.get_dialogs()
        target_chats = [
            dialog.id for dialog in dialogs 
            if dialog.is_group and dialog.id not in DEV_CHAT
        ]
        
        JmdB.set_key("NSHR", True)
        status_msg = await event.edit("**- جاري النشر...**")
        
        total_sent = 0
        total_failed = 0
        
        for _ in range(count):
            if not JmdB.get_key("NSHR"):
                break
            
            sent, failed = await send_to_chats(event.client, message, media, target_chats)
            total_sent += sent
            total_failed += failed
            
            await status_msg.edit(
                f"**📊 إحصائيات النشر:**\n"
                f"✅ الناجح: {total_sent}\n"
                f"❌ الفاشل: {total_failed}"
            )
            await asyncio.sleep(delay)
            
    except (ValueError, IndexError):
        await event.edit("** استخدام خاطئ!**\nالاستخدام: `.نشر [الوقت] [العدد]` بالرد على الرسالة أو `.نشر [الوقت] [العدد] [النص]`")
    except Exception as e:
        LOGS.error(f"خطأ في امر النشر: {e}")
    finally:
        JmdB.del_key("NSHR")

@jmthon_cmd(pattern="ايقاف (النشر|نشر)")
async def stop_nshr(e):
    if JmdB.get_key("NSHR"):
        JmdB.del_key("NSHR")
        await e.respond("**⌔∮ تم إيقاف النشر الوقتي بنجاح!**")
    else:
        await e.respond("**⌔∮أمر النشر ليس قيد التنفيذ حاليًا.**")

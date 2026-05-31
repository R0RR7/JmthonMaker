"""
❃ `{i}منع` <كلمة>
   لـ منع أرسال هذه الكلمة في الدردشة واذا ارسلها مستخدم سيتم حذفها

❃ `{i}الغاء منع` <كلمة>
   لـ الغاء منع الكلمة والسماح للمستخدم ارسالها بدون حذفها

❃ `{i}قائمة المنع` 
    لـ عرض قائمة الكلمات التي منعتها في الدردشة
"""

from telethon import events

from .. import JmdB, jmubot, jmthon_cmd



@jmthon_cmd(pattern="منع( (.*)|$)", admins_only=True)
async def af(e):
    moh = e.pattern_match.group(1).strip()
    chat = e.chat_id
    if not (moh):
        return await e.eor("**⌔∮ يجب عليك كتابة الكلمة المراد منعها مع الامر**", time=5)
    moh = e.text[11:]
    heh = moh.split(" ")
    for z in heh:
        add_blacklist(int(chat), z.lower())
    jmubot.add_handler(blacklist, events.NewMessage(incoming=True))
    await e.eor("**⌔∮ تم بنجاح أضافة الكلمة {} الى قائمة المنع**".format(moh))


@jmthon_cmd(pattern="الغاء منع( (.*)|$)", admins_only=True)
async def ref(e):
    moh = e.pattern_match.group(1).strip()
    chat = e.chat_id
    if not moh:
        return await e.eor("**⌔∮ يجب عليك كتابة الكلمة التي تريد الغاء منعها في الدردشة**", time=5)
    moh = e.text[14:]
    heh = moh.split(" ")
    for z in heh:
        rem_blacklist(int(chat), z.lower())
    await e.eor("**⌔∮ تم بنجاح الغاء منع الكلمة {} والسماح بها**".format(moh))


@jmthon_cmd(pattern="قائمة المنع$", admins_only=True)
async def lsrf(e):
    if x := list_blacklist(e.chat_id):
        sd = "**⌔∮ قائمة الكلمات الممنوع أرسلها في الدردشة**: \n\n"
        return await e.eor(sd + x)
    await e.eor("**⌔∮ لا يوجد أي كلمة ممنوعة في هذه الدردشة**")


async def blacklist(e):
    if x := get_blacklist(e.chat_id):
        text = e.text.lower().split()
        if any((z in text) for z in x):
            try:
                await e.delete()
            except BaseException:
                pass


def get_stuff():
    return JmdB.get_key("BLACKLIST_DB") or {}


def add_blacklist(chat, word):
    ok = get_stuff()
    if ok.get(chat):
        for z in filter(lambda z: z not in ok[chat], word.split()):
            ok[chat].append(z)
    else:
        ok.update({chat: [word]})
    return JmdB.set_key("BLACKLIST_DB", ok)


def rem_blacklist(chat, word):
    ok = get_stuff()
    if ok.get(chat) and word in ok[chat]:
        ok[chat].remove(word)
        return JmdB.set_key("BLACKLIST_DB", ok)


def list_blacklist(chat):
    ok = get_stuff()
    if ok.get(chat):
        txt = "".join(f"❃ `{z}`\n" for z in ok[chat])
        if txt:
            return txt


def get_blacklist(chat):
    ok = get_stuff()
    if ok.get(chat):
        return ok[chat]


if JmdB.get_key("BLACKLIST_DB"):
    jmubot.add_handler(blacklist, events.NewMessage(incoming=True))

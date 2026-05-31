import asyncio
import os
import re
from datetime import datetime, timedelta
from telethon import TelegramClient, Button, events
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, AccessTokenExpiredError, AccessTokenInvalidError

from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID, SUPPORT_USERNAME, FACTORY_DIR

DEV_GROUP = -5066651723
from logger import LOG
import database as db
import deployer

def _main_buttons(user_id):
    if user_id == OWNER_ID:
        return [
            [Button.inline("الاحصائيات", "admin_stats")],
            [Button.inline("تجديد تنصيب", "admin_renew")],
            [Button.inline("أيقاف تنصيب", "admin_delete_user")],
        ]
    btns = [
        [Button.inline("🔧 تنصيب جمثون", "install")],
        [Button.inline("📊 حالة التنصيب", "status"), Button.inline("🔄 إعادة تشغيل", "restart")],
        [Button.inline("🗑 حذف التنصيب", "uninstall")],
        [Button.url("• المطور • ", f"t.me/{SUPPORT_USERNAME}")],
    ]
    return btns


def _admin_buttons():
    return [
        [Button.inline("الاحصائيات", "admin_stats")],
        [Button.inline("تجديد تنصيب", "admin_renew")],
        [Button.inline("أيقاف تنصيب", "admin_delete_user")],
        [Button.inline("🔙 رجوع", "main_menu")],
    ]


class JmthonFactory(TelegramClient):
    def __init__(self):
        for _f in os.listdir(FACTORY_DIR):
            if _f.startswith("JmthonFactory.session"):
                os.remove(os.path.join(FACTORY_DIR, _f))
        super().__init__("JmthonFactory", API_ID, API_HASH)
        self.user_states = {}
        self.temp_clients = {}
        self.loop.run_until_complete(self._async_boot())
        self.add_event_handler(self._on_start, events.NewMessage(pattern="/start$"))
        self.add_event_handler(self._on_cancel, events.NewMessage(pattern="/cancel$"))
        self.add_event_handler(self._on_callback, events.CallbackQuery())
        self.add_event_handler(self._on_message, events.NewMessage(func=lambda e: e.is_private and not e.text.startswith("/")))
        self.loop.create_task(self._resume_deployments())
        self.loop.create_task(self._health_loop())
        LOG.info(f"Factory bot started as @{self.me.username}")

    async def _async_boot(self):
        await self.connect()
        if not await self.is_user_authorized():
            await self.sign_in(bot_token=BOT_TOKEN)
        self.me = await self.get_me()

    async def _verify_file_session(self, uid, data):
        session_name = data.get("session", "")
        if not session_name:
            return False
        dpath = deployer._deploy_path(uid)
        session_full = os.path.join(dpath, session_name)
        try:
            vc = TelegramClient(session_full, data["api_id"], data["api_hash"])
            await vc.connect()
            me = await vc.get_me()
            await vc.disconnect()
            if me is None:
                LOG.error(f"Session verification failed: get_me() returned None for {uid}")
                return False
            LOG.info(f"Session verified for user {me.id} ({uid})")
            return True
        except Exception as e:
            LOG.error(f"Session verification raised for {uid}: {e}")
            return False

    async def _on_cancel(self, event):
        uid = event.sender_id
        self.user_states.pop(uid, None)
        tc = self.temp_clients.pop(uid, None)
        if tc:
            try:
                await tc.disconnect()
            except Exception:
                pass
        await self._send_main(event, "⟐ تم بنجاح الغاء هذه العملية")

    async def _send_main(self, event, text=None):
        uid = event.sender_id
        txt = text or "مرحبا بك في بوت تنصيب سورس جمثون\nاختر أحد الأوامر من القائمة:"
        btns = _main_buttons(uid)
        if isinstance(event, events.CallbackQuery.Event):
            await event.edit(txt, buttons=btns)
        else:
            await event.respond(txt, buttons=btns)

    async def _on_start(self, event):
        uid = event.sender_id
        uname = event.sender.username
        fname = event.sender.first_name or "User"
        db.add_user(uid, uname, fname)
        await self._send_main(event)
        total = len(db.get_all_users())
        try:
            await self.send_message(DEV_GROUP,
                f"👾 **مستخدم جديد في البوت**\n\n"
                f"• الاسم: `{fname}`\n"
                f"• الايدي `{uid}`\n"
                f"• التاريخ: `{datetime.now().strftime('%Y-%m-%d')}`\n"
                f"• عدد مستخدمين البوت : `{total}`"
            )
        except Exception:
            pass

    async def _on_callback(self, event):
        uid = event.sender_id
        data = event.data.decode()

        if data == "main_menu":
            self.user_states.pop(uid, None)
            await self._send_main(event)
            return await event.answer()

        if data == "install":
            user = db.get_user(uid)
            if user and user.get("is_installed") and user.get("status") in ("running", "stopped"):
                return await event.answer("سورس جمثون شغال عندك", alert=True)
            self.user_states[uid] = {"step": "awaiting_token", "data": {"api_id": API_ID, "api_hash": API_HASH}}
            await event.edit("📌 الان أرسل توكن البوت المساعد\n\n• ادخل الى @botfather\n• أرسل /newbot\n• أرسل له اسم البوت\n• ثم أرسل له يوزر ينتهي بـ bot\n• ثم أرسل التوكن هنا \n\n⚡️التوكن عبارة عن رمز مكون من أرقام وحروف مثل:\n`123456789:ABCdefGHI..`", buttons=[[Button.inline("الغاء التنصيب", "cancel")]])
            return await event.answer()

        if data == "status":
            await self._show_status(event, uid)
            return await event.answer()

        if data == "restart":
            await self._do_restart(event, uid)
            return await event.answer()

        if data == "uninstall":
            return await self._confirm_uninstall(event, uid)

        if data == "confirm_uninstall":
            await self._do_uninstall(event, uid)
            return await event.answer()

        if data == "cancel_uninstall":
            self.user_states.pop(uid, None)
            await self._send_main(event)
            return await event.answer()

        if data == "admin_panel":
            if uid != OWNER_ID:
                return await event.answer("ليست لديك صلاحيات", alert=True)
            await event.edit("**- لوحة تحكم المطور**", buttons=_admin_buttons())
            return await event.answer()

        if data == "admin_stats":
            if uid != OWNER_ID:
                return await event.answer("ليست لديك صلاحيات", alert=True)
            s = db.get_stats()
            text = (
                f"👾 **إحصائيات البوت**\n\n"
                f"• إجمالي المستخدمين: `{s['total_users']}`\n"
                f"• المنصبين: `{s['installed']}`\n"
                f"• النشطين: `{s['running']}`\n"
                f"• الموقوفين: `{s['stopped']}`\n"
                f"• منتهية اشتراكاتهم: `{s['expired']}`"
            )
            await event.respond(text)
            return await event.answer()

        if data == "admin_renew":
            if uid != OWNER_ID:
                return await event.answer("ليست لديك صلاحيات", alert=True)
            self.user_states[uid] = {"step": "admin_awaiting_uid", "data": {}}
            await event.edit("أرسل ايدي المستخدم هسة", buttons=[[Button.inline("الغاء", "cancel")]])
            return await event.answer()

        if data == "admin_delete_user":
            if uid != OWNER_ID:
                return await event.answer("ليست لديك صلاحيات", alert=True)
            self.user_states[uid] = {"step": "admin_awaiting_del_uid", "data": {}}
            await event.edit("ارسل ايدي المستخدم هسة", buttons=[[Button.inline("الغاء", "cancel")]])
            return await event.answer()

        if data == "cancel":
            self.user_states.pop(uid, None)
            tc = self.temp_clients.pop(uid, None)
            if tc:
                try:
                    await tc.disconnect()
                except Exception:
                    pass
            await self._send_main(event, "⟐ تم بنجاح الغاء هذه العملية")
            return await event.answer()

    async def _on_message(self, event):
        uid = event.sender_id
        text = event.text.strip()
        state = self.user_states.get(uid)
        if not state:
            return

        step = state["step"]
        data = state["data"]

        if text == "/cancel" or text.lower() == "الغاء":
            self.user_states.pop(uid, None)
            tc = self.temp_clients.pop(uid, None)
            if tc:
                try:
                    await tc.disconnect()
                except Exception:
                    pass
            await self._send_main(event, "⟐ تم بنجاح الغاء هذه العملية")
            await event.delete()
            return

        try:
            if step == "awaiting_token":
                if not re.match(r"^\d+:[\w\-]+$", text):
                    return await event.respond("⟐ توكن البوت غير صحيح يرجى التأكد من التوكن من @botfather")
                msg = await event.respond("🔄 جار التحقق من التوكن...")
                try:
                    tc = TelegramClient(StringSession(), data["api_id"], data["api_hash"])
                    await tc.connect()
                    await tc.sign_in(bot_token=text)
                    bot_me = await tc.get_me()
                    await tc.disconnect()
                except (AccessTokenInvalidError, AccessTokenExpiredError):
                    await msg.edit("⟐ هذا التوكن منتهي الصلاحيات أصنع توكن جديد من @botfather وأرسله")
                    return
                except Exception as e:
                    await msg.edit(f"⟐ لقد حدث خطأ في التحقق من التوكن\n {e}")
                    return
                data["bot_token"] = text
                self.user_states[uid] = {"step": "awaiting_phone", "data": data}
                await msg.edit(f"• تم بنجاح التحقق من البوت @{bot_me.username} ✅\n• أرسل الان رقم الهاتف مع كود الدولة\n• مثل`+96407XXXXXXX`")

            elif step == "awaiting_phone":
                if not text.startswith("+"):
                    return await event.respond("⟐ يجب أن يحتوي الرقم على كود الدولة مثل `+96407XXXXXXX`\n ⟐ أعد عملية التنصيب من جديد الان")
                data["phone"] = text
                self.user_states[uid] = {"step": "awaiting_code", "data": data}
                await self._send_code(event, uid, data)

            elif step == "awaiting_code":
                code = text.replace(" ", "")
                if not code.isdigit() or len(code) < 4:
                    return await event.respond("⟐ يجب أرسال كود التحقق بشكل صحيح مع وضع مسافات")
                await self._verify_code(event, uid, code, data)

            elif step == "awaiting_2fa":
                data["password"] = text
                await self._verify_2fa(event, uid, data)

            elif step == "admin_awaiting_uid":
                if not text.lstrip("-").isdigit():
                    return await event.respond("- أرسل ايدي المستخدم الان")
                data["target_uid"] = int(text)
                self.user_states[uid] = {"step": "admin_awaiting_days", "data": data}
                await event.respond("✅ تم استلام الايدي!\n📅 أرسل **عدد الأيام** للتجديد:")

            elif step == "admin_awaiting_days":
                if not text.isdigit() or int(text) < 1:
                    return await event.respond("❌ أرسل عدد أيام صحيح (رقم > 0):")
                await self._admin_renew(event, uid, data["target_uid"], int(text))

            elif step == "admin_awaiting_del_uid":
                if not text.lstrip("-").isdigit():
                    return await event.respond("❌ أرسل ايدي المستخدم (رقم):")
                await self._admin_delete_install(event, uid, int(text))

        except Exception as e:
            LOG.exception(f"Error in msg handler for {uid}")
            await event.respond(f"❌ حدث خطأ: {e}")
            self.user_states.pop(uid, None)

    async def _send_code(self, event, uid, data):
        try:
            dpath = deployer._deploy_path(uid)
            os.makedirs(dpath, exist_ok=True)
            session_name = f"userbot_{uid}"
            session_full = os.path.join(dpath, session_name)
            for sf in (session_full + ".session", session_full + ".session-journal"):
                if os.path.exists(sf):
                    os.remove(sf)

            client = TelegramClient(session_full, data["api_id"], data["api_hash"])
            await client.connect()
            if await client.is_user_authorized():
                data["session"] = StringSession.save(client.session)
                await self._finalize_install(event, uid, data)
                return

            await client.send_code_request(data["phone"])
            self.temp_clients[uid] = client
            self.user_states[uid] = {"step": "awaiting_code", "data": data}
            await event.respond("""⟐  تم أرسال كود الدخول من التليجرام
⟐  أرسل الكود مع وضع مسافات 
⟐  مثل    1 2 3 4 5""")
        except Exception as e:
            await event.respond(f"⟐ حدثت مشكلة أثناء أرسال الكود\n {e}")
            self.user_states.pop(uid, None)

    async def _verify_code(self, event, uid, code, data):
        client = self.temp_clients.get(uid)
        if not client:
            await event.respond("⟐ أنتهت جلسة البوت يرجى أعادة التنصيب من جديد")
            self.user_states.pop(uid, None)
            return
        try:
            await client.sign_in(data["phone"], code)
            self.temp_clients.pop(uid, None)
            data["session"] = StringSession.save(client.session)
            await self._finalize_install(event, uid, data)
        except SessionPasswordNeededError:
            self.user_states[uid] = {"step": "awaiting_2fa", "data": data}
            await event.respond("⟐ هذا الحساب يحتوي على تحقق بخطوتين \n⟐ يرجى أرسال كلمة المرور الان")
        except PhoneCodeInvalidError:
            await event.respond("⟐ الكود غير صحيح يرجى أرسال الكود بشكل صحيح")
        except Exception as e:
            await event.respond(f"⟐ فشل في عملية تسجيل الدخول يرجى معاودة التنصيب")
            self.temp_clients.pop(uid, None)
            self.user_states.pop(uid, None)

    async def _verify_2fa(self, event, uid, data):
        client = self.temp_clients.get(uid)
        if not client:
            await event.respond("⟐ أنتهت جلسة البوت يرجى أعادة التنصيب من جديد")
            self.user_states.pop(uid, None)
            return
        try:
            await client.sign_in(password=data["password"])
            self.temp_clients.pop(uid, None)
            data["session"] = StringSession.save(client.session)
            await self._finalize_install(event, uid, data)
        except Exception as e:
            await event.respond(f"⟐ فشل في عملية تسجيل الدخول يرجى معاودة التنصيب")
            self.temp_clients.pop(uid, None)
            self.user_states.pop(uid, None)

    async def _session_verify_fail(self, event, uid, data):
        self.user_states.pop(uid, None)
        await event.respond("⟐ فشل في عملية تسجيل الدخول يرجى معاودة التنصيب",
            buttons=_main_buttons(uid),
        )

    async def _finalize_install(self, event, uid, data):
        session_str = data.get("session")
        if not session_str:
            await self._session_verify_fail(event, uid, data)
            return

        env_vars = {
            "API_ID": str(data["api_id"]),
            "API_HASH": data["api_hash"],
            "SESSION": session_str,
            "BOT_TOKEN": data["bot_token"],
        }
        try:
            deployer.deploy(uid, env_vars)
            expiry = (datetime.now() + timedelta(days=3)).isoformat()
            db.update_user(uid,
                is_installed=True,
                install_date=datetime.now().isoformat(),
                expiry_date=expiry,
                phone=data["phone"],
                status="running",
            )
            self.user_states.pop(uid, None)
            await event.respond(
                f"👾 تم تنصيب سورس جمثون بنجاح \n\n",
                f"• لعرض الأوامر أرسل `.الاوامر`\n"
                f"• قناة سورس جمثون @Jmthon",
                buttons=_main_buttons(uid),
            )
        except Exception as e:
            LOG.exception(f"Deploy failed for {uid}")
            await event.respond(f"⟐ فشل في عملية التنصيب يرجى معاودة التنصيب")
            self.user_states.pop(uid, None)

    async def _show_status(self, event, uid):
        user = db.get_user(uid)
        if not user or not user.get("is_installed"):
            return await event.answer("لا يوجد أي تنصيب شغال", alert=True)

        status = user.get("status", "none")
        running = deployer.is_running(uid)
        if running and status != "expired":
            db.update_user(uid, status="running")
            status = "running"
        elif not running and status == "running":
            db.update_user(uid, status="stopped")
            status = "stopped"

        icons = {"running": "🟢", "stopped": "🔴", "expired": "⏰", "none": "⚪"}
        icon = icons.get(status, "⚪")
        status_text = {"running": "شغال", "stopped": "متوقف", "expired": "منتهي", "none": "لا يوجد"}

        uptime = deployer.get_uptime(uid) if running else 0
        uptime_str = f"{uptime // 3600}س {uptime % 3600 // 60}د" if uptime else "—"

        install_date = user.get("install_date", "")
        install_str = datetime.fromisoformat(install_date).strftime("%Y-%m-%d %H:%M") if install_date else "—"

        expiry = user.get("expiry_date", "")
        if expiry:
            exp_dt = datetime.fromisoformat(expiry)
            expiry_str = exp_dt.strftime("%Y-%m-%d %H:%M")
            remaining = (exp_dt - datetime.now()).days if exp_dt > datetime.now() else 0
        else:
            expiry_str = "—"
            remaining = 0

        text = (
            f"👾 حالة تنصيب سورس جمثون\n\n"
            f"• الايدي: {uid}\n"
            f"• الهاتف: `{user.get('phone', '—')}\n"
            f"• تاريخ التنصيب: {install_str}\n"
            f"• الحالة: {status_text.get(status, '—')} {icon} \n"
            f"• شغال منذ: {uptime_str}\n"
            f"• ينتهي في: {expiry_str}\n"
            f"• متبقي: {remaining} يوم"
        )
        await event.edit(text, buttons=[[Button.inline("• رجوع •", "main_menu")]])

    async def _do_restart(self, event, uid):
        user = db.get_user(uid)
        if not user or not user.get("is_installed"):
            return await event.answer("لا يوجد تنصيب لإعادة تشغيله", alert=True)
        if user.get("status") == "expired":
            return await event.answer("اشتراكك منتهي جدد عند المطور @R0R77", alert=True)

        try:
            deployer.restart(uid)
            db.update_user(uid, status="running")
            await event.answer("⟐ تم بنجاح أعادة تشغيل سورس جمثون", alert=True)
        except Exception as e:
            LOG.exception(f"Restart failed for {uid}")
            await event.answer(f"فشل في عملية أعادة التشغيل\n{e}", alert=True)

    async def _confirm_uninstall(self, event, uid):
        btns = [
            [Button.inline("تأكيد الحذف", "confirm_uninstall")],
            [Button.inline("الغاء ", "cancel_uninstall")],
        ]
        await event.edit("هل أنت متأكد من حذف التنصيب ?", buttons=btns)
        return await event.answer()

    async def _do_uninstall(self, event, uid):
        user = db.get_user(uid)
        if not user or not user.get("is_installed"):
            return await event.answer("لا يوجد تنصيب لحذفه", alert=True)

        deployer.cleanup(uid)
        db.update_user(uid,
            is_installed=False,
            install_date=None,
            expiry_date=None,
            phone=None,
            status="none",
        )
        await event.answer("تم حذف التنصيب", alert=True)
        await self._send_main(event, "⟐ تم بنجاح حذف التنصيب من البوت 🗑")

    async def _admin_renew(self, event, uid, target_uid, days):
        target = db.get_user(target_uid)
        if not target:
            self.user_states.pop(uid, None)
            return await event.respond("المستخدم غير موجود.")
        if not target.get("is_installed"):
            self.user_states.pop(uid, None)
            return await event.respond("هذا المستخدم ليس لديه تنصيب")

        new_expiry = (datetime.now() + timedelta(days=days)).isoformat()
        db.update_user(target_uid, expiry_date=new_expiry, status="running")
        if not deployer.is_running(target_uid):
            try:
                deployer.restart(target_uid)
            except Exception:
                pass

        self.user_states.pop(uid, None)
        await event.respond(f"✅ تم تجديد اشتراك المستخدم `{target_uid}` لمدة `{days}` أيام.")
        await self._send_main(event)
        try:
            await self.send_message(target_uid, f"👾 تم تجديد اشتراكك بنجاح\n\n• لمدة: {days} يوم\n\nشكراً لاستخدامك البوت 🙏")
        except Exception:
            pass

    async def _admin_delete_install(self, event, uid, target_uid):
        target = db.get_user(target_uid)
        if not target:
            self.user_states.pop(uid, None)
            return await event.respond("المستخدم غير موجود.")

        deployer.cleanup(target_uid)
        db.delete_user(target_uid)
        self.user_states.pop(uid, None)
        await event.respond(f"✅ تم حذف تنصيب المستخدم `{target_uid}` بالكامل.")
        await self._send_main(event)

    async def _resume_deployments(self):
        LOG.info("Resuming active deployments...")
        for u in db.get_installed_users():
            uid = u["user_id"]
            status = u.get("status")
            if status == "running" and not deployer.is_running(uid):
                try:
                    deployer.restart(uid)
                    LOG.info(f"Resumed deployment for {uid}")
                except Exception as e:
                    LOG.error(f"Failed to resume {uid}: {e}")
                    db.update_user(uid, status="stopped")

    async def _health_loop(self):
        LOG.info("Health check loop started")
        while True:
            try:
                import os as _os
                while True:
                    try:
                        _pid, _exitcode = _os.waitpid(-1, _os.WNOHANG)
                        if _pid <= 0:
                            break
                        LOG.info(f"Reaped zombie child {_pid} (exit={_exitcode})")
                    except ChildProcessError:
                        break
                for u in db.get_installed_users():
                    uid = u["user_id"]
                    expiry = u.get("expiry_date")
                    if expiry and datetime.fromisoformat(expiry) <= datetime.now():
                        if u.get("status") not in ("expired",):
                            deployer.stop(uid)
                            db.update_user(uid, status="expired")
                            try:
                                await self.send_message(uid,
                                    f"أنتهت صلاحية اشتراكك في سورس جمثون\n\n"
                                    f"للتجديد يرجى مراسلة المطور: @{SUPPORT_USERNAME}"
                                )
                            except Exception:
                                pass
                    elif u.get("status") == "running" and not deployer.is_running(uid):
                        db.update_user(uid, status="stopped")
            except Exception as e:
                LOG.error(f"Health check error: {e}")
            await asyncio.sleep(60)

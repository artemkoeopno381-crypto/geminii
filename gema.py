# meta developer: @hikka_and_heroku
# scope: hikka_only

import asyncio
import json
from urllib.request import Request, urlopen
from .. import loader, utils

API_KEY = "AQ.Ab8RN6J_Uk-gryHYoa9d5VEMniVqCpei-MeOvPr70vr1_HsSlQ"
TARGET_CHAT = -1002439987653


@loader.tds
class GeminiAutoChatMod(loader.Module):
    """Авто-ответчик через Gemini AI с тумблером вкл/выкл"""

    strings = {"name": "GeminiAutoChat"}

    def __init__(self):
        self.history = []
        self.active = False  # По умолчанию ВЫКЛЮЧЕНО

    async def geminicmd(self, message):
        """<on/off> - Включить или выключить Gemini в чате"""
        args = utils.get_args_raw(message).lower().strip()

        if args == "on":
            self.active = True
            await utils.answer(
                message, "🤖 <b>Gemini AI успешно ВКЛЮЧЕН!</b>"
            )
        elif args == "off":
            self.active = False
            await utils.answer(
                message, "🛑 <b>Gemini AI ВЫКЛЮЧЕН!</b>"
            )
        else:
            status = "ВКЛЮЧЕН 🟢" if self.active else "ВЫКЛЮЧЕН 🔴"
            await utils.answer(
                message,
                f"ℹ️ Статус ИИ: <b>{status}</b>\n\n"
                f"Использование:\n"
                f"• <code>.gemini on</code> — Включить\n"
                f"• <code>.gemini off</code> — Выключить",
            )

    @loader.watcher()
    async def watcher(self, message):
        # Если выключено — ничего не делаем
        if not self.active:
            return

        if not message.text or getattr(message, "out", False):
            return

        chat_id = utils.get_chat_id(message)
        if chat_id != TARGET_CHAT:
            return

        if message.sender and getattr(message.sender, "bot", False):
            return

        user_text = message.text.strip()
        if len(user_text) < 2 or user_text.startswith("."):
            return

        user_name = (
            message.sender.first_name if message.sender else "Участник"
        )
        self.history.append(
            {"role": "user", "parts": [{"text": f"{user_name}: {user_text}"}]}
        )

        # Экономия токенов: держим максимум 4 сообщения
        if len(self.history) > 4:
            self.history = self.history[-4:]

        system_instruction = (
            "Ты — обычный дерзкий участник этого Telegram-чата. "
            "Отвечай кратко, с юмором или сарказмом, как живой пацан в чате. "
            "Максимум 1-2 коротких предложения!"
        )

        payload = {
            "contents": self.history,
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "generationConfig": {
                "maxOutputTokens": 80,
                "temperature": 0.8,
            },
        }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

        try:
            req = Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: urlopen(req, timeout=10).read()
            )
            data = json.loads(response.decode("utf-8"))

            answer_text = (
                data["candidates"][0]["content"]["parts"][0]["text"].strip()
            )

            self.history.append(
                {"role": "model", "parts": [{"text": answer_text}]}
            )

            await message.reply(answer_text)

        except Exception as e:
            print(f"[Gemini Error]: {e}")

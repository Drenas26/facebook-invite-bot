import asyncio
import logging
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
from clients import GmailnatorClient, FirstmailClient
from config import TELEGRAM_TOKEN, RAPIDAPI_KEY, RAPIDAPI_HOST, FIRSTMAIL_API_KEY

# Настройка таймаутов для запросов к Telegram
request_kwargs = {
    'connect_timeout': 60.0,
    'read_timeout': 60.0,
    'write_timeout': 60.0,
    'pool_timeout': 60.0,
}
request = HTTPXRequest(**request_kwargs)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logging.getLogger("httpx").setLevel(logging.WARNING)

class FacebookInviteBot:
    def __init__(self):
        self.gmailnator = GmailnatorClient(RAPIDAPI_KEY, RAPIDAPI_HOST)
        self.firstmail = FirstmailClient(FIRSTMAIL_API_KEY)
        self.user_service = {}
        self.user_password = {}
        self.MAX_EMAILS = 10
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("📧 Gmailnator", callback_data="service_gmailnator")],
            [InlineKeyboardButton("📧 Firstmail", callback_data="service_firstmail")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🤖 *Facebook Business Manager Invite Bot*\n\n"
            "Выберите сервис временной почты:\n\n"
            "• *Gmailnator* - быстрый, без пароля\n"
            "• *Firstmail* - резервный, требует пароль\n\n"
            "Если один сервис не работает, попробуйте другой.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def service_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        service = query.data.replace("service_", "")
        
        if service == "gmailnator":
            self.user_service[user_id] = "gmailnator"
            await query.edit_message_text(
                "✅ *Выбран сервис: Gmailnator*\n\n"
                "📧 Отправьте email (без пароля)\n\n"
                f"📌 Максимум: {self.MAX_EMAILS} email за раз\n"
                f"⏱ Проверка: 2 проверки (через 7 и 15 секунд)\n\n"
                "Команда /start - выбрать другой сервис",
                parse_mode='Markdown'
            )
        elif service == "firstmail":
            self.user_service[user_id] = "firstmail"
            await query.edit_message_text(
                "✅ *Выбран сервис: Firstmail*\n\n"
                "🔐 Отправьте email и пароль в формате:\n"
                "`email пароль`\n\n"
                "Пример: `prewvckt@polosmail.com ibvjhkpdS!1901`\n\n"
                f"📌 Максимум: {self.MAX_EMAILS} email за раз\n"
                f"⏱ Проверка: 2 проверки (через 7 и 15 секунд)",
                parse_mode='Markdown'
            )
    
    async def handle_emails(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        if user_id not in self.user_service:
            await update.message.reply_text(
                "❌ Сначала выберите сервис командой /start",
                parse_mode='Markdown'
            )
            return
        
        service = self.user_service[user_id]
        
        if service == "gmailnator":
            await self.handle_gmailnator(update, text)
        elif service == "firstmail":
            await self.handle_firstmail(update, text, user_id)
    
    async def handle_gmailnator(self, update: Update, text: str):
        emails = [line.strip() for line in text.split('\n') if line.strip()]
        
        valid_emails = []
        for email in emails:
            if '@' in email and '.' in email:
                valid_emails.append(email)
        
        if len(valid_emails) > self.MAX_EMAILS:
            await update.message.reply_text(
                f"❌ Слишком много email! Максимум: {self.MAX_EMAILS}",
                parse_mode='Markdown'
            )
            return
        
        if not valid_emails:
            await update.message.reply_text("❌ Отправьте корректный email адрес")
            return
        
        numbered_list = "\n".join([f"{i+1}. `{email}`" for i, email in enumerate(valid_emails)])
        await update.message.reply_text(
            f"🚀 *Запускаю обработку {len(valid_emails)} email через Gmailnator...*\n\n"
            f"{numbered_list}\n\n"
            f"⏱ Проверки: через 7 и 15 секунд\n\n"
            f"Ожидайте результаты 👇",
            parse_mode='Markdown'
        )
        
        tasks = []
        for i, email in enumerate(valid_emails):
            task = asyncio.create_task(
                self.process_single_email(update, email, i + 1, "gmailnator")
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def handle_firstmail(self, update: Update, text: str, user_id: int):
        # Формат: email пароль (через пробел)
        parts = text.split()
        
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Для Firstmail укажите email и пароль в формате:\n"
                "`email пароль`\n\n"
                "Пример: `prewvckt@polosmail.com ibvjhkpdS!1901`",
                parse_mode='Markdown'
            )
            return
        
        email = parts[0]
        password = ' '.join(parts[1:])
        
        if '@' not in email or not password:
            await update.message.reply_text("❌ Укажите корректный email и пароль")
            return
        
        self.user_password[user_id] = password
        
        await update.message.reply_text(
            f"🚀 *Запускаю обработку через Firstmail...*\n\n"
            f"📧 `{email}`\n\n"
            f"⏱ Проверки: через 7 и 15 секунд\n\n"
            f"Ожидайте результат 👇",
            parse_mode='Markdown'
        )
        
        await self.process_single_email(update, email, 1, "firstmail", password)
    
    async def process_single_email(self, update: Update, email: str, index: int, service: str, password: str = None) -> Optional[str]:
        client = self.gmailnator if service == "gmailnator" else self.firstmail
        service_name = "Gmailnator" if service == "gmailnator" else "Firstmail"
        
        status_msg = await update.message.reply_text(
            f"#{index} 📧 `{email}` [{service_name}]\n"
            f"🔄 *Статус:* Поиск письма от Facebook...\n"
            f"⏳ Будет выполнено 2 проверки (через 7 и 15 секунд)",
            parse_mode='Markdown'
        )
        
        try:
            invite_link = await asyncio.to_thread(
                client.find_facebook_invite,
                email=email,
                password=password,
                attempts=2,
                interval_first=7,
                interval_second=8
            )
            
            if invite_link:
                await status_msg.edit_text(
                    f"#{index} ✅ *Успешно!* [{service_name}]\n\n"
                    f"📧 `{email}`\n\n"
                    f"🔗 `{invite_link}`",
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                return invite_link
            else:
                await status_msg.edit_text(
                    f"#{index} ❌ *Письмо не обнаружено* [{service_name}]\n\n"
                    f"📧 `{email}`\n\n"
                    f"Отправь приглашение еще раз или используй другой сервис.",
                    parse_mode='Markdown'
                )
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при обработке {email}: {e}")
            await status_msg.edit_text(
                f"#{index} ❌ *Ошибка* [{service_name}]\n\n"
                f"📧 `{email}`\n\n"
                f"```\n{str(e)[:150]}\n```",
                parse_mode='Markdown'
            )
            raise e
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📚 *Инструкция*\n\n"
            "1. Выберите сервис: /start\n"
            "2. Для Gmailnator: отправьте email\n"
            "3. Для Firstmail: отправьте email и пароль в формате:\n"
            "   `email пароль`\n\n"
            f"*Ограничения:*\n"
            f"• Максимум {self.MAX_EMAILS} email за раз\n"
            f"• 2 проверки (через 7 и 15 секунд)\n\n"
            "*Команды:*\n"
            "/start - выбрать сервис\n"
            "/help - справка",
            parse_mode='Markdown'
        )

def main():
    if not TELEGRAM_TOKEN:
        print("❌ Ошибка: TELEGRAM_TOKEN не найден в .env")
        return
    
    print("🤖 Запуск бота...")
    print("✅ Gmailnator клиент готов")
    print("✅ Firstmail клиент готов")
    print("⚙️ Настройки: 2 проверки (через 7 и 15 секунд)")
    
    bot = FacebookInviteBot()
    # Используем кастомный request с таймаутами
    app = Application.builder().token(TELEGRAM_TOKEN).request(request).build()
    
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("help", bot.help_command))
    app.add_handler(CallbackQueryHandler(bot.service_selection, pattern="^service_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_emails))
    
    print("✅ Бот запущен и готов к работе!")
    print("📌 Доступные сервисы: Gmailnator, Firstmail")
    app.run_polling()

if __name__ == "__main__":
    main()
import asyncio
import logging
from typing import Optional
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from gmailnator_client import GmailnatorClient
from config import TELEGRAM_TOKEN, MAX_WAIT_TIME, CHECK_INTERVAL

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Отключаем подробные логи httpx
logging.getLogger("httpx").setLevel(logging.WARNING)

class FacebookInviteBot:
    def __init__(self):
        self.client = GmailnatorClient()
        self.MAX_EMAILS = 10
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 *Facebook Business Manager Invite Bot*\n\n"
            "Я ищу приглашения в Facebook Business Manager.\n\n"
            "*Как отправить несколько email:*\n"
            "Просто отправьте email-адреса каждый с новой строки:\n\n"
            "```\nemail1@gmail.com\nemail2@gmail.com\n```\n\n"
            f"📌 *Максимум:* {self.MAX_EMAILS} email за раз\n"
            f"⏱ *Время ожидания:* {MAX_WAIT_TIME // 60} минут на каждый\n"
            f"🔄 *Проверка:* каждые {CHECK_INTERVAL} секунд\n\n"
            "*Команды:*\n"
            "/start - начать работу\n"
            "/help - справка\n\n"
            "*Как копировать:*\n"
            "• Нажмите и удерживайте на email → скопируется в буфер\n"
            "• Нажмите и удерживайте на ссылке → скопируется в буфер",
            parse_mode='Markdown'
        )
    
    async def handle_emails(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка одного или нескольких email"""
        text = update.message.text.strip()
        
        # Разбиваем текст на строки и фильтруем пустые
        emails = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Валидация email
        valid_emails = []
        invalid_emails = []
        
        for email in emails:
            if '@' in email and '.' in email:
                valid_emails.append(email)
            else:
                invalid_emails.append(email)
        
        # Проверка на количество
        if len(valid_emails) > self.MAX_EMAILS:
            await update.message.reply_text(
                f"❌ *Слишком много email!*\n\n"
                f"Вы отправили {len(valid_emails)} email.\n"
                f"Максимум: *{self.MAX_EMAILS} email* за раз.",
                parse_mode='Markdown'
            )
            return
        
        if invalid_emails:
            await update.message.reply_text(
                f"⚠️ *Некорректные email:*\n`{chr(10).join(invalid_emails)}`",
                parse_mode='Markdown'
            )
        
        if not valid_emails:
            await update.message.reply_text(
                "❌ Не найдено корректных email адресов."
            )
            return
        
        # Отправляем сообщение о начале обработки
        await update.message.reply_text(
            f"🚀 *Запускаю обработку {len(valid_emails)} email...*\n\n"
            f"Ожидайте результаты в отдельных сообщениях ниже 👇",
            parse_mode='Markdown'
        )
        
        # Запускаем параллельную обработку всех email
        tasks = []
        for email in valid_emails:
            task = asyncio.create_task(
                self.process_single_email(update, email)
            )
            tasks.append(task)
        
        # Ждем завершения всех задач
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def process_single_email(self, update: Update, email: str) -> Optional[str]:
        """Обработка одного email в отдельной задаче со своим сообщением"""
        # Отправляем отдельное сообщение для этого email
        status_msg = await update.message.reply_text(
            f"📧 `{email}`\n"
            f"🔄 *Статус:* Поиск письма от Facebook...\n"
            f"⏳ Время ожидания: {MAX_WAIT_TIME // 60} мин",
            parse_mode='Markdown'
        )
        
        try:
            # Запускаем поиск в отдельном потоке
            invite_link = await asyncio.to_thread(
                self.client.find_facebook_invite,
                email=email,
                timeout=MAX_WAIT_TIME,
                check_interval=CHECK_INTERVAL
            )
            
            if invite_link:
                await status_msg.edit_text(
                    f"✅ *Успешно!*\n\n"
                    f"📧 `{email}`\n\n"
                    f"🔗 `{invite_link}`",
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                return invite_link
            else:
                await status_msg.edit_text(
                    f"⏱️ *Не найдено*\n\n"
                    f"📧 `{email}`\n\n"
                    f"Письмо от Facebook не обнаружено за {MAX_WAIT_TIME // 60} минут.",
                    parse_mode='Markdown'
                )
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при обработке {email}: {e}")
            await status_msg.edit_text(
                f"❌ *Ошибка*\n\n"
                f"📧 `{email}`\n\n"
                f"```\n{str(e)[:150]}\n```",
                parse_mode='Markdown'
            )
            raise e
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help - справка"""
        await update.message.reply_text(
            "📚 *Инструкция*\n\n"
            "*Как отправить email:*\n"
            "• Один email: просто отправьте его в чат\n"
            "• Несколько email: каждый с новой строки\n\n"
            "*Пример:*\n"
            "```\nemail1@gmail.com\nemail2@gmail.com\n```\n\n"
            f"*Ограничения:*\n"
            f"• Максимум {self.MAX_EMAILS} email за раз\n"
            f"• Время ожидания: {MAX_WAIT_TIME // 60} мин на каждый\n"
            f"• Проверка: каждые {CHECK_INTERVAL} сек\n\n"
            "*Как копировать:*\n"
            "• Нажмите и удерживайте на email → скопируется в буфер обмена\n"
            "• Нажмите и удерживайте на ссылке → скопируется в буфер обмена\n\n"
            "*Команды:*\n"
            "/start - начать работу\n"
            "/help - показать справку",
            parse_mode='Markdown'
        )

def main():
    if not TELEGRAM_TOKEN:
        print("❌ Ошибка: TELEGRAM_TOKEN не найден в .env")
        print("Создайте файл .env с переменной TELEGRAM_TOKEN")
        return
    
    print("🤖 Запуск бота...")
    print(f"Токен: {TELEGRAM_TOKEN[:15]}...")
    
    bot = FacebookInviteBot()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("help", bot.help_command))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        bot.handle_emails
    ))
    
    print("✅ Бот запущен и готов к работе!")
    print(f"📌 Поддерживается до {bot.MAX_EMAILS} email за раз")
    print("📋 Email и ссылки копируются при удерживании")
    app.run_polling()

if __name__ == "__main__":
    main()
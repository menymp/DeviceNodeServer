from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


#main class handler
class TelegramBotUtil():
	def __init__(self, token):
		self.app = ApplicationBuilder().token(token).build()
		pass
	
	def run(self):
		self.app.run_polling()
	
	def addHandler(self, handler, command):
		self.app.add_handler(CommandHandler(command, handler))
		
#command example
async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello rr {update.effective_user.first_name}')


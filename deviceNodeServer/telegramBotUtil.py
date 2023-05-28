from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from functools import partial

#main class handler
class TelegramBotUtil():
	def __init__(self, token):
		self.app = ApplicationBuilder().token(token).build()
		pass
	
	def run(self):
		self.app.run_polling()
	
	def addHandler(self, handler, command, refArg):
		self.app.add_handler(CommandHandler(command, partial(handler, refArg=refArg)))


from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from functools import partial

#main class handler
class TelegramBotUtil():
	def __init__(self, token):
		self.token = token
		self.definedHandlers = []
		pass
	
	def run(self):
		if not self.token:
			return False
		
		self.app = ApplicationBuilder().token(self.token).build()
		for handler in self.definedHandlers:
			self.addHandler(handler[1],handler[0],handler[2])
			pass
		self.app.run_polling()
	
	def addHandlers(self, handlerList):
		self.definedHandlers = handlerList
		pass

	def addHandler(self, handler, command, refArg):
		self.app.add_handler(CommandHandler(command, partial(handler, refArg=refArg)))


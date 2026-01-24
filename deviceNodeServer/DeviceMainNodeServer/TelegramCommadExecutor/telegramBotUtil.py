from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from functools import partial
from os.path import dirname, realpath, sep, pardir
import sys
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")

from loggerUtils import get_logger
logger = get_logger(__name__)
#main class handler
class TelegramBotUtil():
	def __init__(self, token):
		logger.info("init new telegram bot instance")
		self.token = token
		self.definedHandlers = []
		pass
	
	def run(self):
		if not self.token:
			return False
		logger.info("token available, running")
		self.app = ApplicationBuilder().token(self.token).build()
		for handler in self.definedHandlers:
			self.addHandler(handler[1],handler[0],handler[2])
			pass
		self.app.run_polling()
	
	def stop(self):
		try:
			self.app.stop()
			logger.info("stopping server")
			return True
		except:
			return False

	
	def addHandlers(self, handlerList):
		logger.info("added handlers")
		self.definedHandlers = handlerList
		pass

	def addHandler(self, handler, command, refArg):
		logger.info("added new handler " + str(handler) + " " + str(command) + " " + str(refArg))
		self.app.add_handler(CommandHandler(command, partial(handler, refArg=refArg)))


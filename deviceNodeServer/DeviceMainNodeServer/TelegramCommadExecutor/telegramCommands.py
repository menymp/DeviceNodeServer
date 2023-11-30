#contains the logic for the telegram api telemetry
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegramBotUtil import TelegramBotUtil
import threading
import cv2
import asyncio

import sys
from os.path import dirname, realpath, sep, pardir
# Get current main.py directory
sys.path.append(dirname(realpath(__file__)) + sep + pardir)
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DBUtils")

from dbActions import dbUserActions
#
#objInstances expect to hold the main instances, for now just
# video and device commands
#
#ToDo: expect to refract each existing component and isolate as a single external process
#      to allow scalability and multiple external servers working together
class TelegramCommandExecutor():
	def __init__(self, initArgs, objInstances):
		self.dbHost = initArgs[0]
		self.dbName = initArgs[1]
		self.dbUser = initArgs[2]
		self.dbPass = initArgs[3]
		self.activeUserProcesses = []

		#is this a good approach if the expected number of main apis grows?
		self.definedHandlers = [('hello',hello, None),('devices',deviceCmdHandler, objInstances["devices"]),('cameras',videoCmdHandler, objInstances["cameras"])]
		pass
	
	def start(self):
		userTks = self.fetchUserTokens()
		
		for token in userTks:
			self.initNewUserApi(token[0])
			pass
		pass

	def stop(self):
		for userProcess in self.activeUserProcesses:
			userProcess[1].stop()
	
	def fetchUserTokens(self):
		#checks for users with active tokens to try
		self.dbActions = dbUserActions()
		self.dbActions.initConnector(self.dbUser,self.dbPass,self.dbHost,self.dbName)
		userTks = self.dbActions.getUserTelegramTokens()
		return userTks
	
	def initNewUserApi(self, token):
		#call for init a new user token
		# should a better approach other than the use of a thread for each new user be expected?
		userProcessHandler = TelegramBotUtil(token)
		#for handler in self.definedHandlers:
		#	userProcessHandler.addHandler(handler[1],handler[0],handler[2])
		#	pass
		userProcessHandler.addHandlers(self.definedHandlers)
		userThread = threading.Thread(target=loopThreadForever, args=(userProcessHandler,))
		userThread.start()
		
		self.activeUserProcesses.append((userThread, userProcessHandler))
		pass

def loopThreadForever(telegramBotObject):
	loop = asyncio.new_event_loop()
	asyncio.set_event_loop(loop)
	telegramBotObject.run()
	pass
#command example
#for now just add interface for interaction with devices and cameras

#for command args example
#https://stackoverflow.com/questions/71551866/python-telegram-bot-pass-arguments-to-the-bot
#for object pass as a parameter end of the page
#https://github.com/python-telegram-bot/python-telegram-bot/issues/1002

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE, refArg) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

async def deviceCmdHandler(update: Update, context: ContextTypes.DEFAULT_TYPE, refArg) -> None:
	#execute operations related to the commands
	#the current object returns an array
	result = refArg.execCommand(context.args) # the object is passed as partial refArg
	await update.message.reply_text(result)

async def videoCmdHandler(update: Update, context: ContextTypes.DEFAULT_TYPE, refArg) -> None:
	#execute operations related to the cameras
	result = refArg.execCommand(context.args)
	if result is None:
		return

	if ('ls' in context.args):
		await update.message.reply_text(result)
	elif('get' in context.args):
		imgPath = update.effective_user.first_name.replace(' ','' ) + '.jpg'
		cv2.imwrite(imgPath, result) #ToDo: what happens if user have spaces
		chat_id = update.message.chat_id
		await context.bot.sendPhoto(chat_id=chat_id, photo=imgPath)
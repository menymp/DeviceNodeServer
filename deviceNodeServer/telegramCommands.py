#contains the logic for the telegram api telemetry
from telegramBotUtil import TelegramBotUtil
import threading
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
		self.fetchUserTokens()
		
		for token in userTks:
			self.initNewUserApi(token)
			pass
		pass
	
	def fetchUserTokens(self):
		#checks for users with active tokens to try
		self.dbActions = dbUserActions()
		self.dbActions.initConnector(self.dbUser,self.dbPass,self.dbHost,self.dbName)
		userTks = self.dbActions.getUserTelegramTokens()
		return userTks
	
	def initNewUserApi(self, token):
		#call for init a new user token
		# should a better approach other than the use of a thread for each new user be expected?
		userProcessHandler = TelegramBotUtil()
		for handler in self.definedHandlers:
			userProcessHandler.addHandler(handler[1],handler[0],handler[2])
			pass
		userThread = threading.Thread(target=loopThreadForever, args=(userProcessHandler,))
		userThread.start()
		
		self.activeUserProcesses.append(userThread)
		pass

def loopThreadForever(telegramBotObject):
	telegramBotObject.run()
	pass
#command example
#for now just add interface for interaction with devices and cameras
async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

async def deviceCmdHandler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	#execute operations related to the commands
	#ToDo: just placeholder, test this case
	rawCommandText = userInputArguments ################
	result = args.execCommand(rawCommandText) #############
	await update.message.reply_text(result)

async def videoCmdHandler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	#execute operations related to the cameras
	await update.message.reply_text(f'result {update.effective_user.first_name}')
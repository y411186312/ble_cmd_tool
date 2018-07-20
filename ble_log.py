import sys,time,datetime



class logOprClass:
	def __init__(self, logFolder, logNameHeaderStr, logMutex):
		self._logPath = logFolder + "\\" + logNameHeaderStr + str(time.strftime("_log_%Y_%m_%d_f.txt"))
		self._fileP = None
		self._fileHasBeenClosed = True
		self._writeMutex = logMutex
	
	def _log_is_ok(self):
		return (self._fileP != None)
	
	def _log_init(self):
		try:
			self._fileP = open(self._logPath, "a")
		except:
			print "Error to open log file:", self._logPath
			return False
			
		self._fileHasBeenClosed = False
		return True

	def _log_write_emerge(self, dataString):
		if self._log_is_ok() == False:
			print "log file could not been written, please be check."
			return False
		timeStr = "\n" + "<EMERG_Info>" + "[---- " + str(datetime.datetime.now()) + " ----]" + "\n"
		
		self._writeMutex.acquire()
		try:
			self._fileP.write(timeStr + dataString)
			self._fileP.flush()
		except:
			print "Failed to write log file."
			self._writeMutex.release()
			return False
		print dataString
		self._writeMutex.release()
		return True
		
	def _log_write(self, dataString):	
		if self._log_is_ok() == False:
			print "log file could not been written, please be check."
			return False
			
		self._writeMutex.acquire()
		try:
			self._fileP.write(dataString)
			self._fileP.flush()
		except:
			print "Failed to write log file."
			self._writeMutex.release()
			return False
			
		self._writeMutex.release()
		return True
		
	def _log_close(self):
		if self._log_is_ok() == True and self._fileHasBeenClosed == False:
			self._fileP.close()
			
#end_class
		
'''	
logExam = logOprClass("temps\logs\\")
logExam._log_init()
logExam._log_write("\nhello" + " this is an example" + ">"*10)
'''

import sys,json,serial

class uartOprClass:

	def __init__(self, uart_config_path):
		self._configPath = uart_config_path
		self._serial_p = None
		#self._socketObj = sockObj
		
	def _uart_init(self):
		self._serial_p = serial.Serial()
		try:
			f = open(self._configPath)
		except:
			print "Error to open file:", uart_config_path
			return False
		
		try:
			content = json.load(f)
			self._serial_p.port = content['port']
			self._serial_p.baudrate = content['baudrate']
			self._serial_p.timeout = content['timeout']	# 2s or other
			self._serial_p.stopbits = content['stopbits']
			self._serial_p.parity = content['parity']
			self._serial_p.xonxoff = 0
		except:
			print "Error format uart config file:", self._configPath
			return False
		
		try:
			self._serial_p.open()
		except:
			print "Error to open uart"
			return False
		if self._serial_p.isOpen() == False:
			print("Could not open serial port: %s" % (self._serial_p.port))
			return False
		return True
		
	#true ok, false not ok
	def _uart_is_ok(self):
		try:
			return self._serial_p.isOpen()
		except:
			return False
			
	def _uart_close(self):
		try:
			if self._uart_is_ok() == False:
				self._serial_p.close()
		except:
			self._serial_p = None
			
	#dataLists shoule be format ['0x1','0x2']
	#return [status]
	def _uart_send(self, dataLists):
		sendAssciStr = ''
		if self._serial_p.isOpen() == False:
			print "Uart is not available"
			return False
		try:
			for i in range(len(dataLists)):
				sendAssciStr += chr(int(dataLists[i], 16))
		except:
			print "Error input format."
			return False
			
		try:	
			self._serial_p.write(sendAssciStr)
		except:
			print "Error to write data to uart, please check the data format."
			return False
				
		return True
	
	#return dataLists from uart
	#[dataLists] or None
	def _uart_recv(self):
		dataLists = []
		if self._serial_p.isOpen() == False:
			print "Uart is not available"
			return None
		try:
			firstList = self._serial_p.read(1)
		except:
			print "Serial port is could not be read_1, please be check."
			return None
		if len(firstList) == 0:
			return None
			
		dataLists.append(hex(ord(firstList[0])))
		n = self._serial_p.inWaiting()
		if n > 0:
			try:
				secondList = self._serial_p.read(n)
			except:
				print "Serial port is could not be read_2, please be check."
				return None
				
			for i in range(len(secondList)):
				dataLists.append(hex(ord(secondList[i])))
		return dataLists

#end_class

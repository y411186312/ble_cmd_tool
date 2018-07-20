import sys,os,time

class cmdBufferOprClass:
	def __init__(self, bufFilePath): 
		self._buffer_dic = {}
		self._filePath = bufFilePath
		
	def _cmd_buf_init(self):
		try:
			file_p = open(self._filePath, "r+")
		except:
			print "Failed to open buffer file:",self._filePath
			return False
	
		lines = file_p.readlines() #read all lines
		for line in lines:
			data = line.strip(' ').split(':')	#remove space and split with ':'
			if len(data) == 2:
				self._buffer_dic[data[0]] = data[1]
		file_p.close()
		
	def _cmd_buf_close(self):
		if os.path.exists(self._filePath) == True:
			os.remove(self._filePath)
		
		try:
			file_p = open(self._filePath, "a")
		except:
			print "Failed to open buffer file:",self._filePath
			return False
	
		for key,value in self._buffer_dic.items():
			file_p.write('\n' + key + ":" + value)
		
		file_p.close()
	
	def _cmd_buf_add(self, name, value_list):
		try:
			content = ','.join(value_list)	#list to str, eg: ['0x1', '0x2'] => 0x1,0x2
		except:
			print "Error input."
			return False
		"""
		for key,value in self._buffer_dic.items():
			if cmp(key, name) == 0:
				#update value
				self._buffer_dic[key] = content
				return True
		"""
		try:
			#add new
			self._buffer_dic[name] = content
		except:
			return False
			
		return True
		
	def _cmd_buf_get_list(self, name):
	
		for key,value in self._buffer_dic.items():
			if cmp(key, name) == 0:
				return value.strip(',').split(',')	#str to list, eg: 0x1,0x2,0x3 => ['0x1', '0x2', '0x3']
		
		return None	
	def _cmd_buf_print_all(self):
		for key,value in self._buffer_dic.items():
			print "%s:%s" % (key, value)

'''
cmdBufObj = cmdBufferOprClass("configs\\btc_command_history.ini")
print cmdBufObj._cmd_buf_init()

cmdBufObj._cmd_buf_print_all()
cmdBufObj._cmd_buf_add("hello", ['0x1', '0x2'])
cmdBufObj._cmd_buf_print_all()
print "get:",cmdBufObj._cmd_buf_get_list("hci_le_set_scan_enable")
'''

'''	
a,b = [],[]
a.append(hex(1))
a.append(hex(172))
a.append(hex(4))

b.append(hex(1))
b.append(hex(127))
b.append(hex(4))
b.append(hex(42))


buffer_init("buffer")
buffer_print()
buffer_add("HCI_Reset", a)
buffer_print()
buffer_add("HCI_Reset1", b)

buffer_print()
buffer_close()

print buffer_get_list("HCI_Reset1")
'''
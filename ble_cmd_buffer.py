import sys,os,time

				
class cmdBufferOprClass:
	def __init__(self, bufFilePath): 
		self._buffer_dic = {}
		self._filePath = bufFilePath
		self._comment = ''
		
	def _cmd_buf_init(self):	#add len of parameters, value:0-0xff
		try:
			file_p = open(self._filePath, "r+")
		except:
			print "Failed to open buffer file:",self._filePath
			return False
	
		lines = file_p.readlines() #read all lines
		for line in lines:
			if line[0] == '#':
				self._comment = self._comment + line
				continue	#skip comment
			#xx:OGF xxxx:OCF  defaultValue:xx...
			data = line.strip(' ').strip('\n').split(':')	#remove space and split with ':'
			if len(data) == 2:
				ogf = int('0x' + data[1][0:2], 16)
				ocf = int('0x' + data[1][2:6], 16)
				oprCode = ((ogf & 0x3f) << 10) | (ocf & 0x3ff)
				defaultValueStr = data[1][6:]
				
				valueStr = '%.2x'%(oprCode &0xff) + '%.2x'%((oprCode >> 8) &0xff) + defaultValueStr
				self._buffer_dic[data[0]] = valueStr
				
		file_p.close()
		
	def _cmd_buf_close(self):
		if len(self._buffer_dic) <= 0:
			return
	
		if os.path.exists(self._filePath) == True:
			os.remove(self._filePath)
		
		try:
			file_p = open(self._filePath, "a")
		except:
			print "Failed to open buffer file:",self._filePath
			return False
	
		file_p.write(self._comment)
		"""
		for key,value in self._buffer_dic.items():
		
			oprCode = int('0x' + value[0:2], 16)
			oprCode |= (int('0x' + value[2:4], 16) << 8)
			ogf = (oprCode >> 10) &0x3f
			ocf = oprCode & 0x3ff
			valueStr = '%.2x%.4x'%(ogf,ocf) + '%.2x'%(len(value[6:])/2) + value[6:] #[4:5] for length, db , skip length
			file_p.write('\n' + key + ":" + valueStr)
			
		"""
		for key,value in self._buffer_dic.items():
		
			oprCode = int(value[0:2], 16)
			oprCode |= (int(value[2:4], 16) << 8)
			ogf = (oprCode >> 10) &0x3f
			ocf = oprCode & 0x3ff
			valueStr = '%.2x%.4x'%(ogf,ocf) + value[4:] #
			file_p.write('\n' + key + ":" + valueStr)
		#"""
		file_p.close()
	
	def _cmd_buf_add(self, name, value_list):	#donot save type
		content = ''
		for i in range(1, len(value_list), 1):#skip the first item, do not save type
			content = content + '%.2x'%int(value_list[i], 16)
			
		try:
			#add new
			self._buffer_dic[name] = content
		except:
			return False
			
		return True
		
	def _cmd_buf_get_list(self, name):
		for key,value in self._buffer_dic.items():
			if cmp(key, name) == 0:
				strList = ['0x01']#type
				#print "len:",len(value)
				#print "value:",value
				for i in range(0, len(value),2):
					strList.append('0x' + value[i:i+2])
				return strList
				#return value.strip(',').split(',')	#str to list, eg: 0x1,0x2,0x3 => ['0x1', '0x2', '0x3']
		
		return None	
	def _cmd_buf_print_all(self):
		for key,value in self._buffer_dic.items():
			print "%s:%s" % (key, value)
	#def _cmd_buf_print_org
"""
cmdBufObj = cmdBufferOprClass('temp_config.ini')
cmdBufObj._cmd_buf_init()	
cmdBufObj._cmd_buf_print_all()
print cmdBufObj._cmd_buf_get_list('hci_reset')
print cmdBufObj._cmd_buf_get_list('hci_set_event_mask')	

tempList = ['0x01', '0x02', '0x03', '0x01', '0x05']
cmdBufObj._cmd_buf_add("legend", tempList)
cmdBufObj._cmd_buf_close()
"""
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
import sys,os,time,readline
import ble_common_class as comm_cls
	
class inputOprClass:
	def __init__(self): 
		self._cmdStrLists = []
		self._cmdList = []
		
	def _input_init(self, cmdsList):
		for cmd in cmdsList:
			try:
				self._cmdStrLists.append(cmd._name)
				self._cmdList.append(cmd)
			except:
				print "Input is not class HCI_CMD_CLASS"
				return False
		
		readline.parse_and_bind("tab: complete")
		readline.set_completer(self._completer)
		return True
	
	def _input_remove_tablist(self):
		for i in range(len(self._cmdStrLists)):
			self._cmdStrLists.remove(self._cmdStrLists[0])
			
	def _input_get_tablist(self):
		return self._cmdStrLists
	
	def _input_add_cmd_name(self, nameStr):
		self._cmdStrLists.append(nameStr)
		
	def _input_in_cmdlist(self, inStr):
		for item in self._cmdStrLists:
			if item == inStr:
				return True
		return False
	
	def _completer(self, text, state):
		options = [cmd for cmd in self._cmdStrLists if cmd.startswith(text)]	
	
		#for cmd in 
		if state < len(options):
			return options[state]
		else:
			return None
	
	def _input_get_raw_in(self, title):
		return raw_input(title).strip(' ').strip('\t')#.split()
		
	def _input_get_raw_in_split(self, title, splitTag):
		return raw_input(title).strip(' ').strip('\t').split(splitTag)
	
	def _input_print_input_help(self, cmd_obj):	
		print "Please input all sets of data with hex(without 0x header) separate from a comma."
		print "Each set to split with blank. eg: 01 means int(1), 12 means int(18)"
		contents = 'List:'
		size_str = 'Format:'
		
		print "All: %d sets" % (cmd_obj._paraCounts)
		for i in range(cmd_obj._paraCounts):
			contents = contents + "\n\t" + cmd_obj._paraNameLists[i]
			size_str = size_str + str(cmd_obj._paraSizeLists[i]) + "B,"
			
		size_str = size_str[:-1]
		
		#print "Format..."
		print contents
		print size_str
	
	#None maens need to back previous level, [] means cmdStr invalid
	def _input_get_input_data(self, cmdStr, bufDataList):
		outputList = []
		paraByteList = []
		has_no_buffer = False
		
		if bufDataList != None:
			#means has buffer data
			if len(bufDataList) == 4:	#no parameters need to input
				return bufDataList
				
			print "Enter 'r' to input again, else to use history input."
			r = self._input_get_raw_in('>> ')
			if r != "r":
				return bufDataList
		else:
			has_no_buffer = True
		
		for item in self._cmdList:
			if item._name == cmdStr:
				outputList.append(hex(item._type))
				outputList.append(hex(item._oprCode & 0xff))	#lsb
				outputList.append(hex(item._oprCode >> 8))		#msb
				outputList.append(hex(item._paraLens))			#count

				if has_no_buffer == True:
					print "Enter 'r' to input data, else to use default input(all value: 0x0)."
					r = self._input_get_raw_in('>> ')
					if r != "r":
						if item._paraCounts > 0:
							allLen = 0
							for i in range(item._paraCounts):
								allLen += item._paraSizeLists[i]
							for i in range(allLen):
								outputList.append('0x0')
						break
				
				if item._paraCounts > 0:
					if has_no_buffer == True:
						print "Enter 'r' to input data, else to use default input(all value: 0x0)."
						r = self._input_get_raw_in('>> ')
						if r != "r":
							allLen = 0
							for i in range(item._paraCounts):
								allLen += item._paraSizeLists[i]
							for i in range(allLen):
								outputList.append('0x0')
						break
	
					while True:
						paraByteList = []
						need_input_again = False
						self._input_print_input_help(item)
						orgString = self._input_get_raw_in('input:')
						paraList = orgString.split(',')
						#print "paraList[0]"
						if cmp("back", paraList[0]) == 0:
							print "Back to home."
							return None
							
						#do check 1
						if(len(paraList) != item._paraCounts):
							print "Error input data format."
							for i in range(len(paraList)):
								print "\t",paraList[i]
							continue
						
						#do check 2
						for i in range(item._paraCounts):
							dataList = paraList[i].split()
							#print "len:",len(dataList)
							#print "item._paraSizeLists[i]:",item._paraSizeLists[i]
							#print len(dataList) == item._paraSizeLists[i]
							if len(dataList) != item._paraSizeLists[i]:
								print "Error input dataList format:%s, shoule be %d bytes" % (item._paraNameLists[i], item._paraSizeLists[i])
								need_input_again = True
								break
							for j in range(len(dataList)):
								index = len(dataList) - j - 1	#from last input(lsb), to fill
								temp = '0x' + dataList[index]
								try:
									temp_int = int(temp, 16)
								except:
									need_input_again = True
									print "Error input:", dataList
									break
								paraByteList.append(temp)
								
							#print "data:", data
							if need_input_again == True:
								break
						#print "need_input_again:",need_input_again
						if need_input_again == True:
							continue
						else:
							break
						
				for i in range(len(paraByteList)):
					outputList.append(paraByteList[i])
				break
		return 	outputList
						
	def _input_close(self):
	
		#release memory
		for i in range(len(self._cmdList)):
			self._cmdList.remove(self._cmdList[0])
		
		for i in range(len(self._cmdStrLists)):
			self._cmdStrLists.remove(self._cmdStrLists[0])
		
#end_class
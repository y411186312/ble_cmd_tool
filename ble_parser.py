import sys,os,time,binascii,json
import ble_common_class as comm_cls
import ble_load_data as load_func



#sepc LE_subevent_code.json
class parserOprClass:
	def __init__(self, linkBufObj, resourceFolder, bleSubEventCodeJsonFilePath, connectionList, advDevList):
		self._cmdsList = []
		self._returnPsList = []
		self._eventsList = []
		self._connectionList = connectionList
		self._advDevList = advDevList
		
		self._resFolder = resourceFolder
		self._subEvtCodeJsonPath = bleSubEventCodeJsonFilePath
		self._linkBufObj = linkBufObj
	def _parser_init(self):
		#1. load cmds and returnPs
		self._cmdsList,self._returnPsList = load_func.load_cmds_and_ret_parameters(self._resFolder)
		if self._cmdsList == None or self._returnPsList == None:
			print "Failed to load cmds and return Parameters."
			return False
			
		#2. load events
		self._eventsList = load_func.load_events(self._resFolder, self._subEvtCodeJsonPath)
		if self._eventsList == None:
			print "Failed to load events"
			return False
			
	def _parser_print_cmdsList(self):
		for i in range(len(self._cmdsList)):
			print "\tcmd[%d]:%s" % (i, self._cmdsList[i]._name)
		print "total cmds:", (i + 1)
	def _parser_print_returnparasList(self):
		for i in range(len(self._returnPsList)):
			print "\tretPslist[%d]:%s" % (i, self._returnPsList[i]._name)
		
	def _parser_print_eventsList(self):
		for i in range(len(self._eventsList)):
			print "eventsList[%d]:%s, eventCode=%0#4x" % (i, self._eventsList[i]._name, self._eventsList[i]._eventCode)
	
	def _parser_close(self):
		self._cmdsList = []
		self._returnPsList = []
		self._eventsList = []
		self._advDevList = []
	
	#return [ret, outStr], ret == True is ok, else is not ok
	def _parser_get_out_str(self, evtCode, subEventCode, dataList):	#subEventCode may be None
		offset = 3
		outStr = ""
		isOk = False

		for item in self._eventsList:
			if item._eventCode == evtCode:
				if item._subEventCode == None or (item._subEventCode != None and subEventCode == item._subEventCode):# and subEventCode == item._subEventCode:
					isOk = True
					break

		if isOk == False:
			return [False, outStr]

		outStr = outStr + "\n\t" + "Event name : %s" % item._name
		try:
			for i in range(len(item._paraNameLists)):
				size = item._paraSizeLists[i]
				value = dataList[offset:offset+size]
				if item._paraNameLists[i] != "Data":
					value = list(reversed(value))
					
				if size > 8:
					outStr = outStr + "\n\t" + "%s :[" % item._paraNameLists[i]
					for j in range(len(value)):
						if j % 8 == 0:
							#print "flag3333....."
							outStr = outStr + "\n\t"
						outStr = outStr + str(value[j]) + "  "
					outStr = outStr + "\n\t]"
				else:
					outStr = outStr + "\n\t" + "%s : %s" % (item._paraNameLists[i], str(value)) 
				
				offset += size
		except:
			return [False, outStr]	#packet is insanity
		
		return [True, outStr]
	
	#return [type, eventCode, subEventCode, out_str]: just type = 0x04, eventCode/subEventCode is valid
	def _parser_get_out_str_from_event(self, dateTimeStr, dataList):
		try:
			messageType =  int(dataList[0], 16)
		except:
			return [None, None, None, None]
			
		#outString = '\n\t' + "Data: " +
		outString = ''
		
		eventCode = 0
		subEventCode = None
		payloadLen = None
		
		outString = "-------------------- Time: %s ---------------------" % dateTimeStr
		outString = outString + "\n\t" + "Recv Data: [" + ','.join(dataList) + ' ]'

		if messageType == 0x2: #ACL Data
			ret, tempString = self._parser_get_acl_out_str(dataList)
			if ret == False:
					outString = outString + "\n\tDisconnection_Complete Packet is insanity..."
			else:
				outString = outString + tempString
		
		elif messageType == 0x4: #eventCode
			eventCode = int(dataList[1], 16)
			payloadLen = int(dataList[2], 16)	
			outString = outString + "\n\t" + "Packet Type -> Event Packet : %0#4x" % messageType
			outString = outString + "\n\t" + "Parameter Total Length : %0#4x" % payloadLen
			
			if eventCode == 0x0e:
				ret, tempString = self._parser_command_complete(eventCode, dataList)
				if ret == False:
					outString = outString + "\n\t" + "Command_Complete Packet is insanity..."
				else:
					outString = outString + tempString

			elif eventCode == 0x0f:
				ret, tempString = self._parser_command_status(eventCode, dataList)
				if ret == False:
					outString = outString + "\n\t" + "Command_Status Packet is insanity..."
				else:
					outString = outString + tempString
			
			elif eventCode == 0x05:
				print "Disconnet..."
				ret, tempString = self._parser_disconnection_complete(eventCode, dataList)
				if ret == False:
					outString = outString + "\n\t" + "Disconnection_Complete Packet is insanity..."
				else:
					outString = outString + tempString
			elif eventCode == 0x08:
				ret, tempString = self._parser_encryption_complete(eventCode, dataList)
				if ret == False:
					outString = outString + "\n\t" + "Encryption_CompletePacket is insanity..."
				else:
					outString = outString + tempString
			
			elif eventCode == 0x13:
				ret, tempString = self._parser_num_of_complete_packet(eventCode, dataList)
				if ret == False:
					outString = outString + "\n\t" + "Number_of_Complete_Packets Packet is insanity..."
				else:
					outString = outString + tempString
			elif eventCode == 0x3e:
				ret, tempString = self._parser_le_event_packet(eventCode, dataList)
				if ret == False:
					outString = outString + "\n\t" + "LE_Event_Packets Packet is insanity..."
				else:
					outString = outString + tempString
			else:
				ret, tempString = self._parser_unsupported_event_packet(eventCode, dataList)
				if ret == False:
					outString = outString + "\n\t" + "LE_Event_Packets Packet is insanity..."
				else:
					outString = outString + tempString
					
		return [messageType, eventCode, subEventCode, outString]
	
	#return [ret, outStr], ret == True is ok, else is not ok
	def _parser_unsupported_event_packet(self, evtCode, dataList):
		#1. usual operation
		ret, outStr = self._parser_get_out_str(evtCode, None, dataList)
		if ret == False:
			return [False, outStr]
			
		#2. private opr
		#for nothing to do
		
		return [True, outStr]
	
	
	def _parser_le_enhanced_connection_complete(self, dataList):
		
		print "connection_complete..."
		#print "dataList:",dataList
		connnect = comm_cls.HCI_CONNECT_EVENT_CLASS()
		connnect._subEventCode = int(dataList[3], 16)
		connnect._status = int(dataList[4], 16)
		connnect._connectHandle = int(dataList[5], 16) & 0xff
		connnect._connectHandle |= ((int(dataList[6], 16) & 0x7) << 8)
		connnect._role = int(dataList[7], 16)
		connnect._peerAddrType = int(dataList[8], 16)
		for i in range(6):
			connnect._bdAddr.append(dataList[9 + 5 -i]) #from most to least
			
		for i in range(6):
			connnect._localRpa.append(dataList[15 + 5 -i]) #from most to least
			
		for i in range(6):
			connnect._peerRpa.append(dataList[21 + 5 -i]) #from most to least
			
		connnect._connInterval = int(dataList[27], 16) & 0xff
		connnect._connInterval |= ((int(dataList[28], 16) & 0xff) << 8)
		
		connnect._connLatency = int(dataList[29], 16) & 0xff
		connnect._connLatency |= ((int(dataList[30], 16) & 0xff) << 8)
		
		connnect._timeout = int(dataList[31], 16) & 0xff
		connnect._timeout |= ((int(dataList[32], 16) & 0xff) << 8)
		
		connnect._masterClkAccuracy = int(dataList[33], 16)
		
		
		for i in range(len(self._connectionList)):
			if connnect._connectHandle == self._connectionList[i]._connectHandle:
				self._connectionList.remove(self._connectionList[i])
				break	#remove the same handle object, may be update
		self._connectionList.append(connnect)
	
	def _parser_le_connection_complete(self, dataList):
		
		
		#print "dataList:",dataList
		connnect = comm_cls.HCI_CONNECT_EVENT_CLASS()
		connnect._subEventCode = int(dataList[3], 16)
		connnect._status = int(dataList[4], 16)
		connnect._connectHandle = int(dataList[5], 16) & 0xff
		connnect._connectHandle |= ((int(dataList[6], 16) & 0x7) << 8)
		connnect._role = int(dataList[7], 16)
		connnect._peerAddrType = int(dataList[8], 16)
		for i in range(6):
			connnect._bdAddr.append(dataList[9 + 5 -i]) #from most to least
			
		connnect._connInterval = int(dataList[15], 16) & 0xff
		connnect._connInterval |= ((int(dataList[16], 16) & 0xff) << 8)
		
		connnect._connLatency = int(dataList[17], 16) & 0xff
		connnect._connLatency |= ((int(dataList[18], 16) & 0xff) << 8)
		
		connnect._timeout = int(dataList[19], 16) & 0xff
		connnect._timeout |= ((int(dataList[20], 16) & 0xff) << 8)
		
		connnect._masterClkAccuracy = int(dataList[21], 16)
		
		print "Connect to bd_addr: ", connnect._bdAddr
		for i in range(len(self._connectionList)):
			if connnect._connectHandle == self._connectionList[i]._connectHandle:
				self._connectionList.remove(self._connectionList[i])
				break	#remove the same handle object, may be update
		self._connectionList.append(connnect)
			
	def _parser_le_adv_report(self, dataList):
		bdAddr = dataList[7:7+6]
		bdAddr = bdAddr[::-1]	#reverse list
		
		for i in range(len(self._advDevList)):
			if self._advDevList[i]._bdAddr == bdAddr:
				return True
		advDataLen = int(dataList[14], 16)
		advDev = comm_cls.HCI_ADV_DEVICE_CLASS()
		
		advDev._addrType = int(dataList[6], 16)
		advDev._bdAddr = bdAddr
		advDev._advData = dataList[15:15+advDataLen]
		advDev._rssi = int(dataList[-1], 16)
		self._advDevList.append(advDev)
		return True
		
	
	#return [ret, outStr], ret == True is ok, else is not ok
	def _parser_le_event_packet(self, evtCode, dataList):
		#1. usual operation
		subEvtCode = int(dataList[3], 16)
		
		#print "subEvtCode = 0x%x, len = %d" % (subEvtCode, len(dataList))
		if subEvtCode == 0x02:	#adv report, real len of data need to refill in eventObj
			for i in range(len(self._eventsList)):
				if self._eventsList[i]._subEventCode != None and self._eventsList[i]._subEventCode == subEvtCode:
					#print "before len:",self._eventsList[i]._paraSizeLists[4]
					self._eventsList[i]._paraSizeLists[6] = int(dataList[13], 16)
					#print "after len:",self._eventsList[i]._paraSizeLists[4]
					break
					
			self._parser_le_adv_report(dataList)
			
			
		elif subEvtCode == 0xa and len(dataList) == 34:	#enhanced connect complete event, 22B
			#print "flag1"
			print "enhanced connecting..."
			self._parser_le_connection_complete(dataList)
			
		elif subEvtCode == 0x01 and len(dataList) == 22:	#connect complete event, 22B
			#print "flag1"
			print "connecting..."
			self._parser_le_connection_complete(dataList)
		
		
					
		ret, outStr = self._parser_get_out_str(evtCode, subEvtCode, dataList)
		if ret == False:
			return [False, outStr]
			
		#2. private opr
		return [True, outStr]
	
	#return [ret, outStr], ret == True is ok, else is not ok
	def _parser_num_of_complete_packet(self, evtCode, dataList):
		#1. usual operation
		ret, outStr = self._parser_get_out_str(evtCode, None, dataList)
		if ret == False:
			return [False, outStr]
			
		#2. private opr
		connectHandle = int(dataList[4], 16) & 0xff
		connectHandle |= ((int(dataList[5], 16) & 0x7) << 8)
		
		numOfComplete = int(dataList[6], 16) & 0xff
		numOfComplete |= ((int(dataList[7], 16) & 0x7) << 8)
		
		
		for i in range(len(self._connectionList)):
			if self._connectionList[i]._connectHandle == connectHandle:
				self._connectionList[i]._NumOfCompletePackets = numOfComplete
				self._connectionList[i]._sendComplete = True
				break
		
		return [True, outStr]
		
	#return [ret, outStr], ret == True is ok, else is not ok
	def _parser_encryption_complete(self, evtCode, dataList):
		#1. usual operation
		ret, outStr = self._parser_get_out_str(evtCode, None, dataList)
		if ret == False:
			return [False, outStr]
			
		#2. private opr
		
		return [True, outStr]
		
	#return [ret, outStr], ret == True is ok, else is not ok
	def _parser_disconnection_complete(self, evtCode, dataList):
		#1. usual operation
		ret, outStr = self._parser_get_out_str(evtCode, None, dataList)
		if ret == False:
			return [False, outStr]
			
		#2. private operation
		connectHandle = int(dataList[4], 16) & 0xff
		connectHandle |= ((int(dataList[5], 16) & 0x7) << 8) #12 bits
		for i in range(len(self._connectionList)):
			if self._connectionList[i]._connectHandle == connectHandle:
				self._connectionList[i]._sendThreadQuit = True
				print "Disconnect from bd_addr : %s" % (str(self._connectionList[i]._bdAddr))
				self._connectionList.remove(self._connectionList[i])
				break	#remove disconnect handle
		
		return [True, outStr]
	
	
	def _parser_command_status(self, evtCode, dataList):
		#1. usual operation
		ret, outStr = self._parser_get_out_str(evtCode, None, dataList)
		if ret == False:
			return [False, outStr]
			
		return [True, outStr]
	
	def _parser_command_complete(self, evtCode, dataList):
		hasFound = False
		offset = 6
		#1. usual operation
		ret, outStr = self._parser_get_out_str(evtCode, None, dataList)
		if ret == False:
			print "Error to call _parser_get_out_str"
			return [False, outStr]
	
		#2. parser detail return parameters
		oprCode = int(dataList[4], 16) & 0xff
		oprCode |= ((int(dataList[5], 16) & 0xff) << 8)
		
		if oprCode == 0:
			outStr = outStr + "\n\t" + "Cmd name : No Operation"
			outStr = outStr + "\n\t" + "Num_HCI_Command_Packets : %s" % str(dataList[3:4])
			outStr = outStr + "\n\t" + "Command_Opcode : ['0x0', '0x0']->No Operation"
			return [True, outStr] 
				
		for item in self._returnPsList:
			if item._oprCode == oprCode:
				hasFound = True
				outStr = outStr + "\n\t" + "Cmd name : %s" % item._name
				break
			
		if hasFound == False:
			outStr = outStr + "\n\t" + "Failed to parse packet, error oprcode or db is empty."
			return [False, outStr] 
		
		#"""
		if oprCode == 0x0c03:
			for i in range(len(self._connectionList)):
				print "remove........"
				self._connectionList.remove(self._connectionList[0])
				#remove all connection handle
		#"""			
		if oprCode == 0x2002:
			self._linkBufObj._bufSize = int(dataList[7], 16) & 0xff
			self._linkBufObj._bufSize |= ((int(dataList[8], 16) & 0xff) <<8)
			self._linkBufObj._bufNum = int(dataList[9], 16) & 0xff
			#print "buffer_size = ", self._linkBufObj._bufSize
			#print "buffer_num = ", self._linkBufObj._bufNum
			
		for i in range(len(item._paraNameLists)):
			size = item._paraSizeLists[i]
			outStr = outStr + "\n\t" + "%s : %s" % (item._paraNameLists[i], str(dataList[offset:offset+size]))
			offset += size
		
		return [True, outStr]
	  
	#parse ACL data
	def _parser_get_acl_out_str(self, dataList):
		outStr = ""
		messageType = int(dataList[0], 16)
		#1.1 get acl data packet header and parse them
		Header = int(dataList[1], 16) & 0xff
		Header |= (int(dataList[2], 16) & 0xff) << 8
		Header |= (int(dataList[3], 16) & 0xff) << 16
		Header |= (int(dataList[4], 16) & 0xff) << 24
		connectHandle = Header & 0xfff
		pbFlag = (Header >> 12) & 0x3
		bcFlag = (Header >> 14) & 0x3
		payloadLen = (Header >> 16) & 0xffff
			
		
		#1.2 get output string
		outStr = outStr + "\n\tPacket Type: %0#4x->ACL Data Packet" % messageType
		outStr = outStr + "\n\tConnection_Handle: %0#5x:" % connectHandle
		outStr = outStr + "\n\tPacketBoundary Flag: %0#3x:" % pbFlag
		outStr = outStr + "\n\tBroadCast Flag: %0#3x:" % bcFlag
		outStr = outStr + "\n\tPayLoad_Length: %0#6x:" % payloadLen
		
		outStr = outStr + "\n\t data:"
		realLen = len(dataList) - 5 #1b type, 4b acl header
		for i in range(realLen):
			if i % 8 == 0:
				outStr = outStr + "\n\t"
			outStr = outStr + "  %s" % dataList[i + 5]
		outStr = outStr + "\n"
		return [True, outStr]
#end_class	
		
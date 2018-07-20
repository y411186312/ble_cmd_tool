import sys,time,os,datetime, Queue
import ble_common_class as comm_cls
from  socket import *





# thread_acl_send just send a acl_send cmd
#ctlQueue<mainThread->this:queue> for quit thread, get data from mainThread. data is int(1 for quit)
#aclSendQueue for acl_header, get data from mainThread. data is class 
#aclSendObj<mainThread->this:call> HCI_ACL_SEND_DATA_INFO_CLASS
#type: 0 for recv, 1 for ack
def thread_acl_send(type, connectList, ctlObj, socketClientObj, uartObj, aclSendObj, eventLogObj, fromParserQueue):
	name = sys._getframe().f_code.co_name
	needQuit = False
	hasFoundConnet = False
	
	totalLen = 0
	curLen = 0
	interval = 0	
	allTime = 0
	
	for connect in connectList:
		if connect._connectHandle == aclSendObj._connectionHandle:
			hasFoundConnet = True
			break
		
	if hasFoundConnet == False:
		eventLogObj._log_write_emerge(name + ":" + "Error connect handle, is not available.")
		return
	
	if type == comm_cls.ACK_RECV_DATA_FLAG:	#for recv acl data
		isFirstRecv = True
		previousTime = 0
		firstTime = 0
		
		startTime = time.clock()
		while True:
			if connect._sendThreadQuit == True:
				needQuit = True
				break
				
			while fromParserQueue.qsize() > 0:
				dataFromParser = fromParserQueue.get()
				if dataFromParser._handle != aclSendObj._connectionHandle:
					continue
				totalLen += dataFromParser._recvLen
				if isFirstRecv == True:
					isFirstRecv = False
					interval = 0.1
					allTime = interval
					firstTime = dataFromParser._time
				else:
					interval = dataFromParser._time - firstTime

			if isFirstRecv == False:
				allTime = interval
			else:
				allTime += 0.1
				time.sleep(0.1)
				
			sockSendStr = 'recv'
			sockSendStr = sockSendStr + ',' + hex(totalLen)
			sockSendStr = sockSendStr + ',' + hex(0)
			sockSendStr = sockSendStr + ',' + str(allTime)
			socketClientObj._sockClient.sendto(sockSendStr, socketClientObj._rateSockAddr)	
			
	elif type == comm_cls.ACK_RECV_ACK_FLAG: #for send acl data
		totalLen = aclSendObj._packetSize * aclSendObj._packetCnt
		hasAck = False
		value = 0
		
		for i in range(aclSendObj._packetCnt):
			sendDataList = []
			#1. add header
			sendDataList.append(hex(aclSendObj._type))
			sendDataList.append(hex(aclSendObj._connectionHandle & 0xff))
			sendDataList.append(hex( ((aclSendObj._connectionHandle >> 8) & 0x7) | ((aclSendObj._pbFlag & 0x3) << 4) | ((aclSendObj._pbFlag & 0x3) << 6) ))
			sendDataList.append(hex(aclSendObj._packetSize & 0xff) )
			sendDataList.append(hex((aclSendObj._packetSize >> 8) & 0xff) )
		
			#2. fill data
			for j in range(aclSendObj._packetSize):
				sendDataList.append(hex(value))
				if value >= 0xff:
					value = 0
				else:
					value += 1
					
			#3. get start time
			startTime = time.clock()
			
			#4. send data by uart
			eventLogObj._log_write('\n' + '[ ' + str(datetime.datetime.now()) + ' ] TX ----> ACL data\n' +  \
			                       '\n\t' + 'ACL Packet Len : ' + str(len(sendDataList)) + \
								   '\n\t' + 'ACL Send Data:' + ','.join(sendDataList))
			if uartObj._uart_send(sendDataList) == False:
				eventLogObj._log_write_emerge(name + ":" + "Failed to _uart_send")
				break	#exit thread
			
			#5. wait ack
			hasAck = False
			while True:
				loopStartTime = time.clock()
				if connect._sendThreadQuit == True:
					needQuit = True
					break
				
				while fromParserQueue.qsize() > 0:
					dataFromParser = fromParserQueue.get()
					if dataFromParser._handle == aclSendObj._connectionHandle and dataFromParser._type == comm_cls.ACK_RECV_ACK_FLAG:
						curLen += aclSendObj._packetSize
						interval = time.clock() - startTime
						hasAck = True
				if hasAck != True:
					interval = time.clock() - loopStartTime
					
				allTime += interval
				
				sockSendStr = 'send'
				sockSendStr = sockSendStr + ',' + hex(totalLen)
				sockSendStr = sockSendStr + ',' + hex(curLen)
				sockSendStr = sockSendStr + ',' + str(allTime)
				socketClientObj._sockClient.sendto(sockSendStr, socketClientObj._rateSockAddr)
				if hasAck:
					break	#quit waiting
				continue
			if needQuit == True:
				break
	else:
		eventLogObj._log_write_emerge(name + ":" + "Error type")

	print "Thread < %s > quit..." % (name)
#end_function
	
#for recv data, divide packet
#output: in-queue a event packet, just one packets 
def thread_recv_data(ctlObj, uartObj, eventLogObj, toParserQueue, debugObj):
	name = sys._getframe().f_code.co_name
	remainDataList = []
			
	while ctlObj._allThreadQuit != True:
		recvDataList = uartObj._uart_recv()
		if recvDataList == None:	#no data been read
			continue
		else:
			recvDataList = remainDataList + recvDataList
			remainDataList = []
		
		#check packet is insanity, get remainDataList
		#sendDataObj._dataList = remainDataList + sendDataObj._dataList
		allLen = len(recvDataList)
		offset = 0
		while offset < allLen:
			packetType = int(recvDataList[offset], 16)
			
			toParserDataObj = comm_cls.HCI_QUEUE_RECV_2_PARSER_CLASS()
			toParserDataObj._time = time.clock()
			toParserDataObj._dateTimeStr = str(datetime.datetime.now())
		
			if packetType == 0x04:
				
				try:
					curLen = int(recvDataList[offset + 2], 16)
				except:
					remainDataList = recvDataList[offset:]
					break
					
				if (offset + curLen + 3) <=  allLen:
					toParserDataObj._dataList = recvDataList[offset:offset + curLen + 3]
					toParserQueue.put(toParserDataObj)
					offset += (curLen + 3)
					continue
				else:
					remainDataList = recvDataList[offset:]
					break
			elif packetType == 0x02:
				try:
					curLen = int(recvDataList[offset + 3], 16) & 0xff
					curLen |= ((int(recvDataList[offset + 4], 16) &0xff) << 8)
				except:
					remainDataList = recvDataList[offset:]
					break
				
				if (offset + curLen + 5) <=  allLen:
					toParserDataObj._dataList = recvDataList[offset:offset + curLen + 3]
					toParserQueue.put(toParserDataObj)
					offset += (curLen + 5)
					continue
				else:
					remainDataList = recvDataList[offset:]
					break
			else:
				eventLogObj._log_write_emerge(name + ":" + "Error message type.")
				break
	print "Thread < %s > quit..." % name
#end_function

#parser packet from recv thread, put to main thread to display cmd result, socket send to display event.
def thread_parser(ctlObj, socketClientObj, parserObj, eventLogObj, to_acl_queue, from_recv_queue, to_main_queue, debugObj):
	name = sys._getframe().f_code.co_name
	advMsgQueue = Queue.Queue()
	nonAdvMsgQueue = Queue.Queue()
	
	while ctlObj._allThreadQuit != True:
		packetType, eventCode = -1, -1
		parserOutStr = ''
		qsize = from_recv_queue.qsize()
		
		#1. get all event packet data from recv thread. and in-queue different queue based on packet type
		for i in range(qsize):
			dataFromRecv = from_recv_queue.get()
			if isinstance(dataFromRecv, comm_cls.HCI_QUEUE_RECV_2_PARSER_CLASS) == True:
				packetType = int(dataFromRecv._dataList[0], 16)
				if packetType == 0x4:
					eventCode = int(dataFromRecv._dataList[1], 16)
					subEvtCode = int(dataFromRecv._dataList[3], 16)
					if eventCode == 0x3e and subEvtCode == 0x02:
						advMsgQueue.put(dataFromRecv)
					else:
						nonAdvMsgQueue.put(dataFromRecv)
				else:
					nonAdvMsgQueue.put(dataFromRecv)
			else:
				#add log
				eventLogObj._log_write_emerge(name + ":" + "Get error format data from recv thread.")
				break
		
		#2. process queue ---- priority non-adv packet > adv packet
		#2.1 process non adv packet
		if nonAdvMsgQueue.qsize() > 0:
			#2.1.1 get packet from non-adv queue
			try:
				tempMsgObj = nonAdvMsgQueue.get()
			except:
				break
			
			#2.1.2 parser non-adv packet
			packetType, eventCode, subEventCode, parserOutStr = parserObj._parser_get_out_str_from_event(tempMsgObj._dateTimeStr, \
			                                                                                             tempMsgObj._dataList)
			if packetType == None:
				eventLogObj._log_write_emerge(name + ":" + "Error to process nonAdvMsg.")
				continue
			
			elif packetType == 0x02: 
				#2.1.2.1 recv ACL data
				toAclQueueData = comm_cls.HCI_QUEUE_PARSER_2_ACL_CLASS()
				toAclQueueData._type = comm_cls.ACK_RECV_DATA_FLAG	# 0 for data, 1 for ack
				toAclQueueData._time = tempMsgObj._time
				toAclQueueData._dateTimeStr = tempMsgObj._dateTimeStr
				toAclQueueData._handle = int(tempMsgObj._dataList[1], 16) & 0xff
				toAclQueueData._handle != ((int(tempMsgObj._dataList[2], 16) & 0xf) << 8)
				toAclQueueData._recvLen = int(tempMsgObj._dataList[3], 16) & 0xff
				toAclQueueData._recvLen != ((int(tempMsgObj._dataList[4], 16) & 0xff) << 8)
				to_acl_queue.put(toAclQueueData)
				
			elif eventCode == 0x13:		
				#2.1.2.2 recv ack of ACL send
				toAclQueueData = comm_cls.HCI_QUEUE_PARSER_2_ACL_CLASS()
				toAclQueueData._type = comm_cls.ACK_RECV_ACK_FLAG	# 0 for data, 1 for ack
				toAclQueueData._time = tempMsgObj._time
				toAclQueueData._dateTimeStr = tempMsgObj._dateTimeStr
				toAclQueueData._handle = int(tempMsgObj._dataList[4], 16) & 0xff
				toAclQueueData._handle != ((int(tempMsgObj._dataList[5], 16) & 0xf) << 8)
				to_acl_queue.put(toAclQueueData)
				
			elif eventCode == 0x0f or eventCode == 0x0e:
				#2.1.2.3 recv cmd return parameters, to mainThread to display.
				to_main_queue.put(parserOutStr)	#
				
		#2.2 process adv packet
		elif advMsgQueue.qsize() > 0:
			#2.2.1 get adv packet
			advDataObj = advMsgQueue.get()
			advDataObj._dateTimeStr = advDataObj._dateTimeStr
			#2.2.2 parser adv packet
			packetType, eventCode, subEventCode, parserOutStr = parserObj._parser_get_out_str_from_event(advDataObj._dateTimeStr, advDataObj._dataList)
			if packetType == None:
				eventLogObj._log_write_emerge(name + ":" + "Error to process advMsg.")
				continue
				
		#3. socket to display all event data.
		if len(parserOutStr) > 0:
			eventLogObj._log_write('\n' + '[ ' + str(datetime.datetime.now()) + ' RX <----]\n' + parserOutStr)
			socketClientObj._sockClient.sendto(parserOutStr, socketClientObj._displaySockAddr)
		#else need to sleep?
	#end while
#end_function	
		
		
		
			
		
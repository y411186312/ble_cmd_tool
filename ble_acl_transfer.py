import Queue,threading,sys,os,time

import ble_thread as ble_thread_func
import ble_common_class as comm_cls

def acl_printUsage():
	print "Please input cmd, enter 'help' for more infos..."
	print "\t 'help' to list all supported cmds."
	print "\t 'back' to acl page."
	print "\t 'exit' to home page."
	print "\t 'cancel' to cancel current data transfer."
	print "\t 'list' to list all connect_handle could be used."
	print "\t 'send_data' to list all connect_handle could be used."
#end function
	
def print_connect_handle_infos(connectList):
	try:
		for i in range(len(connectList)):
			print "connect[%d] infos:" % i
			print "\t handle: ", str(connectList[i]._connectHandle)
			print "\t BD Addr: ", str(connectList[i]._bdAddr)
			if connectList[i]._role == 0:
				print "\t Current device is master."
			elif connectList[i]._role == 1:
				print "\t Current device is slave."
		print "Total Len:", len(connectList)
		
	except:
		print "Error connectList format."
#end function	
		
def acl_main(mainArgObj):
	
	cmdList = ['help', 'back', 'cancel', 'list', 'send_data', 'recv_data', 'exit']
	aclSendObj = comm_cls.HCI_ACL_SEND_DATA_INFO_CLASS()
	aclThread = None
	
	os.system("cmd/c start ble_calc_transfer.py")
	#back tab list str
	tabListPtr = mainArgObj._inputClsObj._input_get_tablist()
	backTabList = []
	for i in range(len(tabListPtr)):
		backTabList.append(tabListPtr[i])
	
	mainArgObj._inputClsObj._input_remove_tablist()
	
	for i in range(len(cmdList)):
		mainArgObj._inputClsObj._input_add_cmd_name(cmdList[i])
	
	print_connect_handle_infos(mainArgObj._connectionList)	#list all connection handle
	while True:
		user_in = mainArgObj._inputClsObj._input_get_raw_in("acl>> ")
		if len(user_in) == 0:
			continue
		
		elif cmp(user_in, "help") == 0:
			acl_printUsage()
			continue
			
		elif cmp(user_in, "exit") == 0:
			if aclThread != None and aclThread.isAlive() == True:
				#1. quit 
				for i in range(len(mainArgObj._connectionList)):
					if aclSendObj._connectionHandle == mainArgObj._connectionList[i]._connectHandle:
						mainArgObj._connectionList[i]._sendThreadQuit = True
						break
			break
			
		elif cmp(user_in, "list") == 0:
			print "len(mainArgObj._connectionList):", len(mainArgObj._connectionList)
			print_connect_handle_infos(mainArgObj._connectionList)
			continue
		
		elif cmp(user_in, "cancel") == 0:
			if aclThread != None and aclThread.isAlive() == True:
				#1. quit 
				for i in range(len(mainArgObj._connectionList)):
					if aclSendObj._connectionHandle == mainArgObj._connectionList[i]._connectHandle:
						mainArgObj._connectionList[i]._sendThreadQuit = True
						print "cancel thread..."
						break
				print "Wait..."
				aclThread.join() #wait send data thread to quit.
				aclThread = None
			continue
			
		elif cmp(user_in, "back") == 0:
			
			if aclThread != None and aclThread.isAlive() == True:
				#1. quit 
				for i in range(len(mainArgObj._connectionList)):
					if aclSendObj._connectionHandle == mainArgObj._connectionList[i]._connectHandle:
						mainArgObj._connectionList[i]._sendThreadQuit = True
						break
				print "Wait..."
				#aclThread.join() #wait send data thread to quit.
				
			break
		elif cmp(user_in, "recv_data") == 0:
			handle = 0
			print "recv..."
			if aclThread != None and aclThread.isAlive():
				print "acl is sending, please be waiting..."
				continue
			while True:
				print "Please input handle(hex format)"
				valueStr = mainArgObj._inputClsObj._input_get_raw_in("handleID:")
				if cmp(valueStr, "back") == 0:
					break
				try:
					handle = int(valueStr, 16)
				except:
					print "Error input format."
					continue
				break
			if handle == 0:
				continue
			aclSendObj._connectionHandle = handle
				
			for i in range(len(mainArgObj._connectionList)):
				if aclSendObj._connectionHandle == mainArgObj._connectionList[i]._connectHandle:
					mainArgObj._connectionList[i]._sendThreadQuit = False
					break
			aclThread = threading.Thread(target=ble_thread_func.thread_acl_send, \
	                             args=( comm_cls.ACK_RECV_DATA_FLAG, \
										mainArgObj._connectionList ,\
										mainArgObj._ctlThreadObj, \
										mainArgObj._socketClientObj, \
										mainArgObj._uartClsObj, \
										aclSendObj, \
										mainArgObj._logClsObj, \
										mainArgObj._parser2AclQueue,))
										
			aclThread.start()
			
				
			
				
		elif cmp(user_in, "send_data") == 0:
			if aclThread != None and aclThread.isAlive():
				print "acl is sending, please be waiting..."
				continue
				
			while True:
				print "Please input handle(hex format), packet_size[1-27], packet_cnt[1:], with tag ',' to split them"
				print "e.g: 'x,y,z' means handle is x, packet_size = y, packet_cnt = z."
				print "input 'back' to back to previous page."
				valueList = mainArgObj._inputClsObj._input_get_raw_in_split("input:", ',')
				if len(valueList) == 1:
					if cmp(valueList[0], "back") == 0:
						break
				elif len(valueList) != 3:
					print "Error format input."
					continue
				
				try:
					aclSendObj._connectionHandle = int(valueList[0], 16)
					aclSendObj._packetSize = int(valueList[1], 16)
					aclSendObj._packetCnt = int(valueList[2], 16)
				except:
					print "Error format input:", str(valueList)
					continue
				if aclSendObj._packetSize > 27:
					print "Error packet size, max is 27, 0x19."
					continue
				break
				
			for i in range(len(mainArgObj._connectionList)):
				if aclSendObj._connectionHandle == mainArgObj._connectionList[i]._connectHandle:
					mainArgObj._connectionList[i]._sendThreadQuit = False
					break
			
			aclThread = threading.Thread(target=ble_thread_func.thread_acl_send, \
	                             args=( comm_cls.ACK_RECV_ACK_FLAG, \
										mainArgObj._connectionList, \
										mainArgObj._ctlThreadObj, \
										mainArgObj._socketClientObj, \
										mainArgObj._uartClsObj, \
										aclSendObj, \
										mainArgObj._logClsObj, \
										mainArgObj._parser2AclQueue, ))
			aclThread.start()
		elif cmp(user_in, "rev_data") == 0:
			
			print "recv..."
		
	print "Wait..."	
	if aclThread != None:
		aclThread.join()	#wait 

	#clean memory and restore tab list
	for i in range(len(tabListPtr)):
		tabListPtr.remove(tabListPtr[0])
		
	for i in range(len(backTabList)):
		tabListPtr.append(backTabList[i])
	
	for i in range(len(backTabList)):
		backTabList.remove(backTabList[0])
	mainArgObj._socketClientObj._sockClient.sendto("exit", mainArgObj._socketClientObj._rateSockAddr)

#end function

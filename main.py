import sys,os,time,signal,datetime,threading
from multiprocessing  import Queue

import ble_common_class as comm_cls
import ble_thread as thread_func
import ble_acl_transfer as acl_func

LOG_FOLDER="temps\logs\\"
RESOURCE_FOLDER="spec\\"
UART_CONFIG_PATH="configs\\uart_conf.json"
BLE_SUBEVT_CODE_JSON_PATH="configs\\LE_subevent_code.json"
CMD_BUFFER_FILE="configs\\btc_command_history.ini"
DEBUG_FLAG=False

def global_init(mainObj):
	if mainObj._logClsObj._log_init() == False:
		print "Error to call _logClsObj._log_init"
		return False	
	
	if mainObj._uartClsObj._uart_init() == False:
		print "Error to call _uart_init"
		return False
	
	if mainObj._parserClsObj._parser_init() == False:
		print "Error to call _parser_init"
		return False
	
	if mainObj._cmdBufClsObj._cmd_buf_init() == False:
		print "Error to call _cmd_buf_init"
		return False
		
	if mainObj._inputClsObj._input_init(mainObj._parserClsObj._cmdsList) == False:
		print "Error to call _input_init"
		return False
	
	
	return True
#end_function

def global_close(mainObj):
	mainObj._logClsObj._log_close()
	mainObj._uartClsObj._uart_close()
	mainObj._parserClsObj._parser_close()
	mainObj._cmdBufClsObj._cmd_buf_close()
	mainObj._inputClsObj._input_close()
#end_function	

def main(argv):
	ret = False
	exit_app = False
	
	#1. create class uart/log/parser and do some init
	mainArgObj = comm_cls.MAIN_ARGS_CLASS(UART_CONFIG_PATH, LOG_FOLDER, RESOURCE_FOLDER, BLE_SUBEVT_CODE_JSON_PATH,CMD_BUFFER_FILE, DEBUG_FLAG)
		
	ret = global_init(mainArgObj)
	if ret == False:
		print "Failed to call global_init"
		global_close(mainArgObj)
		sys.exit(1)
		
	mainArgObj._logClsObj._log_write('\n' + '<---------------------------- App Start ---------------------------->')
	mainArgObj._logClsObj._log_write('\n' + '<---------------- ' + str(datetime.datetime.now()) + ' ---------------->')
	print "Please input cmd, enter 'help' for more infos..."
	print "\t 'adv_list' to list all adv, eg: 'adv_list,0' to list detail info of the 1st."
	print "\t 'help' to list all supported cmds."
	print "\t 'clean' to clean env."
	print "\t 'exit' to quit app."
	
	
	mainArgObj._inputClsObj._input_add_cmd_name("help")
	mainArgObj._inputClsObj._input_add_cmd_name("exit")
	mainArgObj._inputClsObj._input_add_cmd_name("clean")
	mainArgObj._inputClsObj._input_add_cmd_name("acl_transfer")
	mainArgObj._inputClsObj._input_add_cmd_name("adv_list")
	
	#2. Create Process to display event/acl data
	os.system("cmd/c start ble_event_transfer.py")
	time.sleep(0.2)
	
	#3. Create thread
	uartRecvThread = threading.Thread(target=	thread_func.thread_recv_data, \
	                                  args  =(	mainArgObj._ctlThreadObj, \
												mainArgObj._uartClsObj, \
												mainArgObj._logClsObj, \
												mainArgObj._recv2ParserQueue, \
												mainArgObj._debugClsObj))
	parserThread = threading.Thread(target=	thread_func.thread_parser, \
	                                args=(	mainArgObj._ctlThreadObj, \
											mainArgObj._socketClientObj, \
											mainArgObj._parserClsObj, \
											mainArgObj._logClsObj, \
											mainArgObj._parser2AclQueue, \
											mainArgObj._recv2ParserQueue, \
											mainArgObj._parser2MainQueue, \
											mainArgObj._debugClsObj))
	uartRecvThread.start()
	parserThread.start()
	
	while exit_app == False:
		#get user in, and process
		user_in = mainArgObj._inputClsObj._input_get_raw_in(">> ")
		if len(user_in) == 0:
			continue
			
		elif cmp(user_in, "exit") == 0:
			print "exit app..."
			mainArgObj._ctlThreadObj._allThreadQuit = True
			exit_app = True
			continue
			
		elif cmp(user_in, "help") == 0:
			mainArgObj._parserClsObj._parser_print_cmdsList()
			continue
		
		elif cmp(user_in, "clean") == 0:
			while mainArgObj._parser2MainQueue.empty() != True:
				tempStr = mainArgObj._parser2MainQueue.get(2)
			continue
		elif cmp(user_in[0:8], "adv_list") == 0:
			advCnt = len(mainArgObj._advDeviceList)
			argList = user_in.split(',')
			if len(argList) == 1:
				for i in range(advCnt):
					print "\tadv[%d] : %s" % (i, mainArgObj._advDeviceList[i]._bdAddr)
			elif len(argList) == 2:
				try:
					advIndex = int(argList[1])
				except:
					mainArgObj._logClsObj._log_write_emerge("Error adv_list index, decimal format.:" + user_in)
					continue
					
				if advIndex >= advCnt:
					mainArgObj._logClsObj._log_write_emerge("Invalid adv_list index, max: %d"% (advCnt-1))
					continue
			
				print "Adv[%d] detail Info:" % advIndex
				print "\taddrType: ", mainArgObj._advDeviceList[advIndex]._addrType
				print "\tbdAddr: ", mainArgObj._advDeviceList[advIndex]._bdAddr
				print "\tadvData: ", mainArgObj._advDeviceList[advIndex]._advData
				print "\trssi: ", hex(mainArgObj._advDeviceList[advIndex]._rssi)
				print "----------------------------------------------"
			else:
				mainArgObj._logClsObj._log_write_emerge("Error adv_list args: " + user_in)
				continue
			
			
		elif cmp(user_in, "acl_transfer") == 0:
			print "acl_transfer data...."
			acl_func.acl_main(mainArgObj)
			continue
			
		elif mainArgObj._inputClsObj._input_in_cmdlist(user_in) == True:
			if user_in == 'hci_reset':
				for i in range(len(mainArgObj._advDeviceList)):
					mainArgObj._advDeviceList.remove(mainArgObj._advDeviceList[0])
		
			#1. check if has cmd input buffer value in this
			bufSendDataList = mainArgObj._cmdBufClsObj._cmd_buf_get_list(user_in)
			
			#2. if not, need to input
			sendDataList = mainArgObj._inputClsObj._input_get_input_data(user_in, bufSendDataList)
			if sendDataList == None or len(sendDataList) == 0:	#do nothing
				continue
			
			#skip some unusing data
			while mainArgObj._parser2MainQueue.empty() != True:
				tempStr = mainArgObj._parser2MainQueue.get()
			mainArgObj._logClsObj._log_write('\n' + '[ ' + str(datetime.datetime.now()) + ' ] TX ----> cmd : %s\n'% user_in + "\n\tCmd Data:" + ','.join(sendDataList))
			print "\nCmd Send Packet Len: ", len(sendDataList)
			print "Cmd Send Data List: \n[\n"
			for i in range(len(sendDataList)):
				if i % 8 == 0 and i != 0:
					print "\n\t"
				print "  %s" % sendDataList[i],
			print "\n]\n"
			
			#3. send cmd
			mainArgObj._uartClsObj._uart_send(sendDataList)
			
			#4. wait result, maybe timeout.
			try:
				outStr = mainArgObj._parser2MainQueue.get(True, 2)
				print outStr
			except:
				mainArgObj._logClsObj._log_write_emerge("Timeout...")
				
			#5. add cmd input buffer to buffer file
			mainArgObj._cmdBufClsObj._cmd_buf_add(user_in, sendDataList)
			continue
			
		else:
			mainArgObj._logClsObj._log_write_emerge("Unkown cmd:" + user_in)
			continue
	#end_while
	
	#wait child thread to quit
	print "main wait..."
	mainArgObj._logClsObj._log_write('\n' + '<------------ app exit ------------>') 
	uartRecvThread.join()
	parserThread.join()
	global_close(mainArgObj)
	mainArgObj._socketClientObj._sockClient.sendto("exit", mainArgObj._socketClientObj._rateSockAddr)
	mainArgObj._socketClientObj._sockClient.sendto("exit", mainArgObj._socketClientObj._displaySockAddr)
	
#end_function	
	

if __name__ == "__main__":
	main(sys.argv)	#main(sys.argv[1:]) means point??? skip app name

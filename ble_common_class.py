

ACK_RECV_DATA_FLAG=0
ACK_RECV_ACK_FLAG=1


class HCI_CMD_CLASS(object):
	def __init__(self):
		self._isCmd = True  #False
		self._isEvent = False
		self._type = 0x01
		self._name = ''
		self._ogf = 0
		self._ocf = 0
		self._oprCode = 0
		self._paraLens = 0
		self._paraCounts = 0			# 2
		self._paraNameLists = []		# {"name1", "name2"}
		self._paraSizeLists = []		# {4, 2}
		#self._sendDataLen = 0			
		self._sendData = [] 			#  need to get from user


		
class HCI_EVENT_CLASS(object):
	def __init__(self):
		self._type = 0x04
		self._name = ''
		self._subEventCode = None		# for LE will be have value
		self._advDataLen = 0			# for LE, just Adv report is valid
		self._eventCode = 0
		self._paraLens = 0
		self._paraCounts = 0			# 
		self._paraNameLists = []		# {"name1", "name2"}
		self._paraSizeLists = []		# {4, 2}
		#self._sendDataLen = 0		
		
class HCI_CONNECT_EVENT_CLASS(object):	# if get LE_Connection_Complete event will init this class obj
	def __init__(self):
		self._sendComplete = False		#True could continue to send
		self._sendThreadQuit = False 	#To control thread quit
		#self._isMaster = True	#default is master
		self._subEventCode = 0	#1B 
		self._status = 1		#1B default '1' could not be used, 0 for ok. 
		self._connectHandle = 0	#2B integer
		self._NumOfCompletePackets = 1		# for acl send...
		self._role = 0			#1B int, 0for master 1 for slave
		self._peerAddrType = 0	#1B int
		self._bdAddr = []		#6B 
		self._localRpa = []		#6B for enhanced connection
		self._peerRpa = []		#6B for enhanced connection
		self._connInterval = 0	#2B integer
		self._connLatency = 0	#2B integer
		self._timeout = 0		#2B integer
		self._masterClkAccuracy = 0 #1B
		
					
class HCI_ACL_SEND_DATA_INFO_CLASS(object):
	def __init__(self):
		self._type = 0x2			#1B always is 0x2
		self._connectionHandle = 0	#2B, 0 for could not available
		self._pbFlag = 0			#1B
		self._bcFlag = 0			#1B
		self._payloayLen = 0		#2B
		self._packetCnt = 1			#default is 1 packet
		self._packetSize = 27		#the maxi size 27
		

class HCI_QUEUE_ACL_2_PARSER_CLASS(object):
	def __init__(self):
		self._time = 0			#int value is time.clock()
		self._totalLen = 0
		self._curLen = 0

class HCI_QUEUE_RECV_2_PARSER_CLASS(object):
	def __init__(self):
		self._dateTimeStr = ''
		self._time = 0			#int value is time.clock()
		self._dataList = []

class HCI_QUEUE_PARSER_2_ACL_CLASS(object):
	def __init__(self):
		self._type = 0			# acl data is 0, ack is 1
		self._handle = 0		#
		self._time	= 0
		self._dateTimeStr = ''
		self._recvLen	= 0			#valid if  _type = 0
		
		
import ble_uart as uart_func
import ble_log as log_func
import ble_parser as parser_func
import ble_cmd_buffer as buf_func
import ble_input as input_func


import Queue,threading
from  socket import *


class MAIN_ARGS_CTL_THREAD_OBJECT(object):
	def __init__(self):
		self._aclThreadQuit = False
		self._allThreadQuit = False
	
class MAIN_ARGS_SOCKET_OBJECT(object):
	def __init__(self):
		self._rateSockAddr = ('localhost', 10001)
		self._displaySockAddr = ('localhost', 10002)
		self._sockClient = socket(AF_INET, SOCK_DGRAM)

class HCI_ADV_DEVICE_CLASS(object):
	def __init__(self):
		self._addrType = 0
		self._bdAddr = []
		self._advData = []
		self._rssi = 0

class HCI_BUFFER_SIZE_CLASS(object):
	def __init__(self):
		self._bufSize = 0
		self._bufNum = []
		
class HCI_DEBUG_CLASS:
	def __init__(self, debug):
		self._debug = debug
		
	def _printDebug(self, str):
		try:
			if self._debug == True:
				print str,'\n'
		except:
			self._debug = self._debug
	
	
#end_class

class MAIN_ARGS_CLASS(object):
	def __init__(self, uartConfigPath, logFolder, resFolder, bleSubEvtJsonFPath, cmdBufFilePath, debugFlag):
		#self._bufferSize = 0
		#self._bufferNum = 0
		
		self._connectionList = []	#HCI_CONNECT_EVENT_CLASS obj list
		self._advDeviceList = []	#HCI_ADV_DEVICE_CLASS obj list
		self._parser2AclQueue = Queue.Queue()	#send start time
		#self._acl2ParserQueue = Queue.Queue()	#send start time
		self._recv2ParserQueue = Queue.Queue()	#send time and recv_data
		self._parser2MainQueue = Queue.Queue()	#send exec results of cmd
		#self._parser2MainQueue = Queue.Queue()	#send exec results of cmd
		self._linkBufObj = HCI_BUFFER_SIZE_CLASS()
		self._ctlThreadObj = MAIN_ARGS_CTL_THREAD_OBJECT()
		self._socketClientObj = MAIN_ARGS_SOCKET_OBJECT()
				
		self._logMutex = threading.Lock()
		self._logClsObj = log_func.logOprClass(logFolder, "event", self._logMutex)
		self._uartClsObj = uart_func.uartOprClass(uartConfigPath)
		self._parserClsObj = parser_func.parserOprClass(self._linkBufObj, resFolder, bleSubEvtJsonFPath, self._connectionList, self._advDeviceList)
		self._cmdBufClsObj = buf_func.cmdBufferOprClass(cmdBufFilePath)
		self._inputClsObj = input_func.inputOprClass()
		self._debugClsObj = HCI_DEBUG_CLASS(debugFlag)
		#self._connectObj = HCI_CONNECTION_CLASS()
		#self._mainCtlQueue = Queue.Queue()	#ctrl parserTHread and recvThread to quit.
		
	
		#self._allThreadQuit = False	#mainThread write, the rest thread just could be read
		#self._aclThreadQuit = False	#mainThread write, the rest thread just could be read
		#self._rateSockAddr = ('localhost', 10001)
		#self._displaySockAddr = ('localhost', 10002)
		#self._sockClient = socket(AF_INET, SOCK_DGRAM)
		
		
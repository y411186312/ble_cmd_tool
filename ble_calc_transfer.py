import sys,time

import sys,os,time,json,serial,string,threading

from  socket import *

HOST=''
PORT=10001
BUFSIZE=1024
ADDR=(HOST,PORT)




#1. v = _curLen / _interval * 8 bps
class HCI_TX_STATUS_CLASS(object):
	def __init__(self):
		self._allLen = 0	#unit Byte
		self._curLen = 0	#
		self._interval = 0.1#unit second
		
def calc_transfer_process(directionID, txClsObj):
	#print "enter..."
	
	
	if directionID == 0: #recv
		process_bar = ''
		sys.stdout.write(process_bar)
		sys.stdout.flush()
		
		rate = txClsObj._allLen * 8 / txClsObj._interval #bps
		tagCnt = txClsObj._allLen / 8
		
		lineCnt = 0
		#if tagCnt == 0:
		#	process_bar = process_bar + '\r'
			
		"""
		for i in range(tagCnt):
			if i % 40 == 0:
				process_bar = process_bar + '\n\t'
				lineCnt += 1
			#print "#"
			process_bar = process_bar + '#'
		#if tagCnt > 0:
		#	print "data:",process_bar
			
		if tagCnt > 0:
			process_bar = process_bar + '\n'
		
		"""
		process_bar = process_bar + '---------------------< avg: ' + '%.2f' % rate + ' bps > < Recv: %d Bytes >---------------------' % txClsObj._allLen + '\r'
		
		#if tagCnt == 0:
		#	process_bar += '\r'
		
		for i in range(lineCnt + 1):
			process_bar += '\r'
	elif directionID == 1:	#send 
		allSteps = 40
		curStep = (txClsObj._curLen * allSteps) / txClsObj._allLen 
		
		if curStep == 0:
			curStep = 1
		rate = txClsObj._curLen * 8 / txClsObj._interval #bps
		process_bar = ''
		sys.stdout.write(process_bar)
		sys.stdout.flush()
		for i in range(curStep):
			process_bar = '[' + '>' * (i+1) + '-' * (allSteps - i - 1) + ']'\
						+ ' <%d bytes> '% txClsObj._curLen + '  <' + '%.2f' % rate + 'bps>' + '\r' 
	else:
		return
	#print "process_bar:",process_bar
	sys.stdout.write(process_bar)
	sys.stdout.flush()
#will get data from socket allLen,cuelen,interval eg: "0x12,0x2,2" means: allLen = 18B, curLen=2B, interval = 2S
def display_to_terminal(dataStr):
	txObj = HCI_TX_STATUS_CLASS()
	#1. connect socket
	dataList = dataStr.strip(' ').split(',')
	#print "dataList:",dataList
	if len(dataList) != 4:
		print "return"
		return
	
	directionID = 0 #0 for recv, 1 for send
	if cmp(dataList[0], "send") == 0:
		directionID = 1
		
	elif cmp(dataList[0], "recv") == 0:
		directionID = 0
	else:
		print "Error data format"
		return
		
	txObj._allLen = int(dataList[1], 16)
	txObj._curLen = int(dataList[2], 16)
	txObj._interval = float(dataList[3])
	
	#print "directionID:",directionID
	calc_transfer_process(directionID, txObj)

	
	



def socket_init():
	global udpSock
	try:
		udpSock = socket(AF_INET, SOCK_DGRAM)
		udpSock.bind(ADDR)
	except Exception,e:
		print "Error to init socket:",e
		return False
	
	return True
	

if False == socket_init():
	print "Failed to socket_init"
	print "ready to quit..."
	time.sleep(2)
	sys.exit(1)
	
while True:
	try:
		data,addr = udpSock.recvfrom(BUFSIZE)
		if data == 'exit':
			print "Ready to quit..."
			time.sleep(2)
			break
		#print "data:",data
		#dataStr = ','.join(data)
		#print "dataStr:"
		#if len(dataStr) != 3:
		#	print "Error dat from udp client:.", addr
		display_to_terminal(data)
		#print data
	except Exception,e:
		print "Error:",e

udpSock.close()


"""
#1. get data from socket
allLen = 2550
curLen = 0

for i in range(25):
	list = []
	allLen = 2550
	curLen += 2550/25
	time.sleep(0.2)
	list.append(hex(allLen))
	list.append(hex(curLen))
	list.append(hex(i + 2))
	dataStr = ','.join(list)
	
	display_to_terminal(dataStr)
	#break
	#2. display
	
"""	
#HCI_TX_STATUS_CLASS
"""
HOST='localhost'
PORT=10000
BUFSIZE=1024
ADDR=(HOST,PORT)

udpSockClient = socket(AF_INET, SOCK_DGRAM)

while True:
	try:
		data = raw_input('>>')
		if not data:
			break
		udpSockClient.sendto(data, ADDR)
		if data == 'quit':
			break
	except Exception,e:
		print "Error:",e
		
udpSockClient.close()
"""
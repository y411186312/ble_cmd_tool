import sys,os,time,json,serial,string,threading

from  socket import *
#from subprocess import *

HOST=''
PORT=10002
BUFSIZE=1024
ADDR=(HOST,PORT)


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
	time.sleep(5)
	sys.exit(1)
	
while True:
	try:
		data,addr = udpSock.recvfrom(BUFSIZE)
		if data == 'exit':
			print "Ready to quit..."
			time.sleep(1)
			break
		print data
	except Exception,e:
		print "Error:",e

udpSock.close()

'''
sock = socket.socket()
host = socket.gethostname() 
port = 12345
addr = (host, port)
sock.bind(addr)

sock.listen(1)
c,addr = sock.accept()
print "addr:",addr
while True:
	
	data = c.recv(1024)
	print "data recv:", data
	if data == 'quit':
		break
	
'''
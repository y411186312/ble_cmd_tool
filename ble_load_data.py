import sys,os,time,binascii,json
import ble_common_class as comm_cls


#name OGF
fileToOgfArray = [
	["LinkControlCommands", 0x1],
	["Link_Policy_Commands", 0x2],
	["Controller_Baseband_Commands", 0x3],
	["Informational_Parameters_Commands", 0x4],
	["Status_Parameters_Commands", 0x05],
	["Testing_Commands", 0x6],
	["Vendor_Commands", 0x3f],
	["LE_Commands", 0x8],
]

event_file_list = [
	"HCI_Events.data"
]
EVENT_DATA_SUFFIX = "_Return_Parameter.data"

packetType = [
	" ",
	"Cmd Packet",
	"ACL Data Packet",
	"Sync Packet",
	"Event Packet"
]


def line_is_empty(line_str):
	if line_str.find("{", 0) < 0:
		return False
	else:
		if line_str.find("}", 1) < 0:
			return False
		else:
			return True

#return [name_x,name_y,name_z],[size_x, size_y,size_z]
def parse_line_cmd_parameter(para_str, count):
	name_list,size_list = [], []
	err_out = [None, None]
	if count <= 0:
		return err_out
	header=tail=0
	for i in range(count):
		header = para_str.find("\"", tail)
		tail = para_str.find("\"", header + 1)
		if tail < header:
			return err_out
		content = para_str[header+1: tail]
		name = content
		
		header = para_str.find(",", tail)
		tail = para_str.find(",", header + 1)
		if tail < header:
			return None

		content = para_str[header+1: tail].strip('}')
		#print "content:",content
		try:
			size = int(content)
		except:
			print "Error %s size." % (name)
			return err_out
		name_list.append(name)
		size_list.append(size)
	return [name_list, size_list]
		
# return Hci_cmds_cls() != None for ok
def parse_line_cmd(org_str, ogf):
	name = sys._getframe().f_code.co_name
	hci_cmd_obj = comm_cls.HCI_CMD_CLASS()
	hci_cmd_obj._ogf = ogf
	header=tail=0
	#print "------------------------------------------"
	
	#print "parse_line_cmd org_str:", org_str
	#1. find cmd name
	header = org_str.find("\"", tail)
	tail = org_str.find("\"", header + 1)
	if tail <= header:
		return None
	content = org_str[header+1: tail]
	#print "content:",content
	hci_cmd_obj._name = content.lower()
	#print "cmd:",hci_cmd_obj._cmd
	
	#2. find ocf
	header = org_str.find(",", tail)
	tail = org_str.find(",", header + 1)
	if tail < header:
		return None

	content = org_str[header+1: tail]
	try:
		hci_cmd_obj._ocf = int(content, 16)
		#print "ocf:",hci_cmd_obj._ocf
	except:
		print "Error ocf format, cmd:", hci_cmd_obj._name
		return None
	
	#hci_cmd_obj._oprCode = hci_cmd_obj._
	
	hci_cmd_obj._oprCode = (hci_cmd_obj._ocf & 0x3ff) | ((hci_cmd_obj._ogf & 0x3f) << 10)
	#3. find paramtere counts
	header = org_str.find(",", tail)
	tail = org_str.find(",", header + 1)
	if tail < header:
		return None
		
	content = org_str[header+1: tail].strip('}')
	try:
		hci_cmd_obj._paraCounts = int(content)
	except:
		print "Error parameters size, cmd:", hci_cmd_obj._name
		return None
	#print "count:",hci_cmd_obj._paraCounts
	
	if hci_cmd_obj._paraCounts == 0:
		return hci_cmd_obj
	
		
	#4. parse paramteres
	name_list, size_list = parse_line_cmd_parameter(org_str[tail:] ,hci_cmd_obj._paraCounts)
	if name_list != None and size_list != None:
		hci_cmd_obj._paraNameLists = name_list
		hci_cmd_obj._paraSizeLists = size_list
		for i in range(len(size_list)):
			hci_cmd_obj._paraLens =  hci_cmd_obj._paraLens + int(size_list[i])
	else:
		return None
	#print "hci_cmd_obj:",hci_cmd_obj
	return hci_cmd_obj
	
def load_cmds_from_file(path, ogf):
	cmd_lists_array = []
	try:
		file = open(path)
	except:
		print ("Error to open :", path)
		return None
	lines = file.readlines() #read all lines
	if len(lines) > 0:
		for line in lines:
			if line_is_empty(line) == False:
				continue
			line = line.strip('\n')	# remove the '\n'	
			cmd_lists = parse_line_cmd(line, ogf)
			if cmd_lists == None:
				print "Error on line:", line
				return None
			cmd_lists_array.append(cmd_lists)
	return cmd_lists_array

	
def load_cmds_and_ret_parameters(folder_str):
	list = os.listdir(folder_str)
	cmds_list = []
	return_para_lists = []
	for file in list:
		for item in fileToOgfArray:
			if cmp(file[0:len(item[0])], item[0]) == 0:
				isCmd = True
				if cmp(file[len(item[0]):], EVENT_DATA_SUFFIX) == 0:
					isCmd = False
					#print "is event"
				
				ogf = item[1]
				#hci_cmd_obj = Hci_cmds_cls()
				#hci_cmd_obj._ogf = item[1]
				path = folder_str + "\\" + file
				one_file_cmds = load_cmds_from_file(path, ogf)
				if one_file_cmds == None:
					print "Error format on file:", path
					return [None, None]
				for cmd in one_file_cmds:
					if isCmd == False:
						cmd._isCmd = False
						return_para_lists.append(cmd)
					else:
						cmd._isCmd = True
						cmds_list.append(cmd)
					#cmds_list.append(cmd)
				break
		
		
	return [cmds_list, return_para_lists]
	
	
#########################################




# return Hci_cmds_cls() != None for ok
def parse_line_event(org_str):
	global subeventJsonObj
	name = sys._getframe().f_code.co_name
	hci_evt_obj = comm_cls.HCI_EVENT_CLASS()
	
	header=tail=0
	#print "------------------------------------------"
	
	#print "parse_line_cmd org_str:", org_str
	#1. find cmd name
	header = org_str.find("\"", tail)
	tail = org_str.find("\"", header + 1)
	if tail <= header:
		return None
	content = org_str[header+1: tail]
	#print "content:",content
	hci_evt_obj._name = content
	#print "cmd:",hci_cmd_obj._cmd
	
	#2. find eventType
	header = org_str.find(",", tail)
	tail = org_str.find(",", header + 1)
	if tail < header:
		return None

	content = org_str[header+1: tail]
	try:
		hci_evt_obj._eventCode = int(content, 16)
		#print "ocf:",hci_cmd_obj._ocf
	except:
		print "Error eventType format, cmd:", hci_evt_obj._name
		return None
	#3. find paramtere counts
	header = org_str.find(",", tail)
	tail = org_str.find(",", header + 1)
	if tail < header:
		return None
		
	content = org_str[header+1: tail].strip('}')
	try:
		hci_evt_obj._paraCounts = int(content)
	except:
		print "Error parameters size, cmd:", hci_evt_obj._name
		return None
	#print "count:",hci_cmd_obj._paraCounts
	
	if hci_evt_obj._paraCounts == 0:
		return hci_evt_obj
	
		
	#4. parse paramteres
	name_list, size_list = parse_line_cmd_parameter(org_str[tail:] ,hci_evt_obj._paraCounts)
	if name_list != None and size_list != None:
		hci_evt_obj._paraNameLists = name_list
		hci_evt_obj._paraSizeLists = size_list
		for i in range(len(size_list)):
			hci_evt_obj._paraLens =  hci_evt_obj._paraLens + int(size_list[i])
	else:
		return None
	#print "hci_evt_obj.name:",hci_evt_obj._name
	
	#fill sub_event_code
	
	if subeventJsonObj.get(hci_evt_obj._name) != None:
		hci_evt_obj._subEventCode = int(subeventJsonObj[hci_evt_obj._name], 16)
		#print "name: %s, subcode:%x" % (hci_evt_obj._name, hci_evt_obj._subEventCode)
	return hci_evt_obj

def load_events_from_file(path):
	event_lists_array = []
	try:
		file = open(path)
	except:
		print ("Error to open :", path)
		return None
	lines = file.readlines() #read all lines
	if len(lines) > 0:
		for line in lines:
			if line_is_empty(line) == False:
				continue
			line = line.strip('\n')	# remove the '\n'	
			event_list = parse_line_event(line)
			if event_list == None:
				print "Error on line:", line
				return None
			event_lists_array.append(event_list)
	return event_lists_array
	
def load_events(folder_str, leSubeventCodeFilePath):
	global subeventJsonObj
	event_list = []
	
	try:
		#print "flag1"
		f = open(leSubeventCodeFilePath)
		#print "flag2"
		subeventJsonObj = json.load(f)
		#print "flag3"
	except:
		print "Error to load json file:", leSubeventCodeFilePath
		return event_list
		
	list = os.listdir(folder_str)
	
	for file in list:
		#print "file:",file
		for item in event_file_list:
			#print "item:",item
			if cmp(file, item) == 0:
				file_path = folder_str + '\\' + file
				one_file_evts = load_events_from_file(file_path)
				
				for event in one_file_evts:
					event_list.append(event)
	
	return event_list
#local development fix
if __name__ == '__main__':
 import sys
 sys.path.append('../')

update_folder = 'update'

from state import State
from u2py.interface_basis import DumpableStructure,DATE,TIME
from u2py.events import Event
from u2py.config import hall_id,hall_device_id
from u2py.stoplist import Stoplist
from datetime import datetime
from ctypes import *
import urllib2
import os

ptCommand = 0
ptAnswer  = 1

cmdGetLastEventNo	= 1
cmdGetEvents		= 2
cmdGetState		    = 3
cmdUpdate		    = 4
cmdRestore		    = 5
cmdRestart		    = 6
cmdSyncTime		    = 7

answOK              = 0
answErrTimeOut      = 1
answErrUnknownCmd   = 2
answErrUpdate       = 3
answErrConnect      = 4
answBadParam        = 5
answBusy            = 6
answNumbersOK       = 7
answNotRunning      = 8
answErrDB           = 9

stWaiting   = 1
stNeedLogin = 2
stWorking   = 3

btNone         = 0 # нет блоков
btEvent        = 1 # блок ответа
btState        = 2 # блок ответа
btGetNumbers   = 3 # блок ответа
btFile         = 4 # блок команды
btTime         = 5 # блок команды
btSetNumbers   = 6 # блок команды
btLimit        = 7 # блок команды/ответа
btCntrState    = 8 # блок команды

command_block_types  = {}
answer_block_types   = {}
commands             = {}

def register(container,key=None,value=None):
 def decorator(cls):
  k = key or cls
  v = value or cls
  container[k] = v
  return cls
 return decorator

class SCommand(DumpableStructure):
 _pack_ = 1
 _fields_ = [
    ('cmd'        ,c_uint8),
    ('event'      ,c_uint32),
    ('count'      ,c_int32),
    ('block_type' ,c_uint8),
    ('block_count',c_int32),
 ]
 _dumpable_ = ['blocks']

 def recv_blocks(self,socket):
  if self.block_type:
   block_type = command_block_types[self.block_type]
   self.blocks = [block_type.from_buffer_copy(socket.recv(sizeof(block_type)))
                  for i in xrange(self.block_count)]
   return self.blocks

 @classmethod
 def recv(cls,socket):
  command = cls.from_buffer_copy(socket.recv(sizeof(cls)))
  command.recv_blocks(socket)
  return command

 def handle(self):
  return commands[self.cmd](self)

class SAnswer(DumpableStructure):
 _pack_ = 1
 _fields_ = [
    ('err_code'   ,c_uint8),
    ('block_type' ,c_uint8),
    ('block_count',c_int32),
 ]
 _dumpable_ = ['blocks']

 def __init__(self,err = answOK,blocks = None):
  if not blocks: blocks = []
  self.err_code = err
  self.block_count = len(blocks)
  self.block_type = answer_block_types[type(blocks[0])] if self.block_count else btNone
  self.blocks = blocks

 def full_sizeof(self):
  return sum([sizeof(block) for block in self.blocks]) + sizeof(self)

 def data(self):
  return ''.join([buffer(block)[:] for block in [self] + self.blocks])

class SPacket(DumpableStructure):
 _pack_ = 1
 _fields_ = [
    ('size',c_uint32),
    ('packet_type',c_uint8),
 ]
 _dumpable_ = ['command','answer']

 def recv_command(self,socket):
  self.command = SCommand.recv(socket)
  return self.command

 @classmethod
 def recv(cls,socket):
  packet = cls.from_buffer_copy(socket.recv(sizeof(cls)))
  packet.recv_command(socket)
  packet.crc = socket.recv(2).encode('hex')
  return packet

 def __init__(self,answer=None):
  self.size = 0
  self.command = None
  self.answer = None
  self.crc = '3412'

  if answer: self.set_answer(answer)

 def set_answer(self,answer):
  self.answer = answer

  self.size = sizeof(self) + self.answer.full_sizeof() + 2
  self.packet_type = ptAnswer

 def send(self,socket):
  if not self.size: return
  a_data = [ buffer(self)[:] ]
  if self.packet_type == ptAnswer: a_data.append(self.answer.data())
  a_data.append(self.crc.decode('hex'))

  data = ''.join(a_data)
  #print data.encode('hex')
  socket.send(data)

@register(command_block_types,key = btFile)
class SFileBlock(DumpableStructure):
 _pack_ = 1
 _fields_ = [
    ('filename',c_char*255),
    ('md5',c_char*32)
 ]

@register(command_block_types,key = btTime)
class STimeBlock(DumpableStructure):
 _pack_ = 1
 _fields_ = [
    ('time',TIME),
    ('date',DATE)
 ]

 def __init__(self,value):
  date_time = datetime.strptime(value,'%Y-%m-%d %H:%M:%S')
  self.time = TIME(time = date_time)
  self.date = DATE(date = date_time)

class SBillAcceptor(DumpableStructure):
 _pack_ = 1
 _fields_ = [
    ('enabled' ,c_uint8),
    ('err_code',c_uint8),
    ('money'   ,c_uint32),
 ]

class SCardReader(DumpableStructure):
 _pack_ = 1
 _fields_ = [
    ('enabled' ,c_uint8),
    ('err_code',c_uint8),
    ('hw_ver'  ,c_char*8),
    ('sn'      ,c_char*8),
 ]

class SVideoSystem(DumpableStructure):
 _pack_ = 1
 _fields_ = [
    ('enabled' ,c_uint8),
    ('err_code',c_uint8),
 ]

class SPrinter(DumpableStructure):
 _pack_ = 1
 _fields_ = [
    ('enabled'     ,c_uint8),
    ('err_code'    ,c_uint8),
    ('check_remain',c_int32),
 ]

@register(answer_block_types,value = btState)
class SStateBlock(DumpableStructure):
 _pack_ = 1
 _fields_ = [
    ('bill'    ,SBillAcceptor),
    ('card'    ,SCardReader),
    ('video'   ,SVideoSystem),
    ('printer' ,SPrinter),
    ('sw_ver'  ,c_char*10),
    ('state'   ,c_uint8)
 ]

@register(answer_block_types,value = btEvent)
class FLASHEVENT(DumpableStructure):
 _pack_ = 1
 _fields_ = [
    ('EventNumber'   ,c_uint32),
    ('Time'          ,STimeBlock),
    ('HallID'        ,c_uint16),
    ('HallDeviceID'  ,c_uint8),
    ('HallDeviceType',c_uint8),
    ('EventCode'     ,c_uint8),
    ('ErrorCode'     ,c_uint8),
    ('DataLen'       ,c_uint8),
    ('EventData'     ,c_uint8*51),
 ]

 def __init__(self,event):
  self.EventNumber    = event.id
  self.Time           = STimeBlock(event.Time)
  self.HallID         = hall_id
  self.HallDeviceID   = hall_device_id
  self.HallDeviceType = 2 # ADBK device type
  self.EventCode      = event.EventCode
  self.ErrorCode      = event.ErrorCode
  self.DataLen        = sizeof(event)
  memmove(addressof(self.EventData),addressof(event),sizeof(event))

@register(commands,key = cmdGetLastEventNo)
def get_last_event_no(command):
 last = Event.load_last()
 event = FLASHEVENT(last)
 return SAnswer(blocks = [event])

@register(commands,key = cmdGetState)
def get_state(command):
 state = SStateBlock()
 state.state = stWorking
 state.sw_ver = 'KI.O1'
 state.card.enabled = 1
 state.card.hw_ver = '001'
 state.card.sn = 'ABCDEF'.decode('hex')

 return SAnswer(blocks = [state])

def handle_stoplist(stoplist):
 lines = stoplist.splitlines()
 version = int(lines[0])
 cards = lines[6:]
 State.set_stoplist_version(version)
 Stoplist.save(card.split() for card in cards)

@register(commands,key = cmdUpdate)
def update(command):
 print command
 if not len(command.blocks): return

 filename = command.blocks[0].filename
 basename = os.path.basename(filename)
 remote = urllib2.urlopen(filename)

 if basename == 'stop_list.stl':
  handle_stoplist(remote.read())
 else:
  local = open(os.path.join(update_folder,basename),'w')
  local.write(remote.read())
  local.close()

 return SAnswer()

@register(commands,key = cmdSyncTime)
def sync_time(command):
 State.update_server_activity()
 return SAnswer()

@register(commands,key = cmdGetEvents)
def get_events(command):
 borders = command.event,command.event+command.count
 limits = min(*borders),max(*borders)-1
 blocks = [FLASHEVENT(event) for event in Event.load(limits)]
 return SAnswer(blocks = blocks)

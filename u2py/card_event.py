from interface_basis import DumpableStructure,DumpableBigEndianStructure,DATE,TIME
from interface import ByteArray
from ctypes import c_uint8,c_uint16,c_uint32,c_uint64,pointer,POINTER,cast,sizeof
from config import db_filename,hall_id,hall_device_id,device_type

EVENT_SECTOR = 3
EVENT_SECTOR_KEY = 7
EVENTS_PER_SECTOR = 3

class AppStatus(DumpableBigEndianStructure):
 _pack_ = 1
 _fields_ = [
    ('id',            c_uint8),
    ('version',       c_uint8,6),
    ('bitmap',        c_uint8,2),
    ('_a',            ByteArray(5)),
    ('_b',            c_uint16,6),
    ('record',        c_uint16,4),
    ('_c',            c_uint16,6),
    ('_d',            ByteArray(7)),
 ]

class AppSectorData(DumpableStructure):
 _pack_ = 1
 _fields_ = [
    ('status',        AppStatus*2)
 ]

class CardEvent(DumpableStructure):
 'fits into one block = 16 bytes'
 _pack_ = 1
 _fields_ = [
    ('id',            c_uint8),
    ('date',          DATE),
    ('time',          TIME),
    ('aid',           c_uint32,12),
    ('place',         c_uint32,12),
    ('device_type',   c_uint32,4),
    ('device_number', c_uint32,4),
    ('transaction',   c_uint16),
    ('event_code',    c_uint8),
    ('code_event',    c_uint32,4),
    ('price',         c_uint32,20),
    ('_checksum',     c_uint32,8)
 ]

 _dumpable_ = ['is_checksum_valid']

 def __init__(self,event,transaction):
  self.id = 0x84
  self.date = DATE()
  self.time = TIME()
  self.aid = 0xD01
  self.place = hall_id
  self.device_type = device_type
  self.device_number = hall_device_id
  self.transaction = transaction
  self.event_code = event.EventCode
  self.code_event = event.TransactionType
  self.price = event.card_event_price()
  self._checksum = self.checksum()

 def checksum(self,check = None):
  raw_bytes = cast(pointer(self),POINTER(c_uint8*sizeof(self))).contents[:-1]
  return reduce(lambda x,y: x^y, raw_bytes)

 def is_checksum_valid(self):
  return self.checksum() == self._checksum

 def next_record(self,card):
  app_sector = card.sector(num=5, key=6, blocks=(0,))
  app_status = AppSectorData.validate(app_sector.data).status[0]
  app_status.record = (app_status.record + 1) % 6
  app_sector.write_block(0)
  return app_status.record

 def save(self,card):
  next_record = self.next_record(card)

  event_sector_num = EVENT_SECTOR + (next_record / EVENTS_PER_SECTOR)
  event_sector = card.sector(num = event_sector_num, key = EVENT_SECTOR_KEY, blocks=())

  event_list = EventList.validate(event_sector.data)
  event_block_num = next_record % EVENTS_PER_SECTOR
  event_list.events[event_block_num] = self
  event_sector.write_block(event_block_num)

class EventList(DumpableStructure):
 _pack_ = 1
 _fields_ = [
    ('events',         CardEvent*3)
 ]

def read(card):
 event_sector1 = card.sector(num = EVENT_SECTOR    ,key = EVENT_SECTOR_KEY)
 event_sector2 = card.sector(num = EVENT_SECTOR + 1,key = EVENT_SECTOR_KEY)

 return EventList.validate(event_sector1.data).events[:] + \
        EventList.validate(event_sector2.data).events[:]

if __name__ == '__main__':
 from interface import Reader
 import transport_card

 card = Reader().scan()

 transport_card.validate(card=card)

 print read(card)
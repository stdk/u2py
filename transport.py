import u2py.config
u2py.config.lib_filename = '../u2lib/libu2.so'

from u2py.interface import DumpableStructure,Reader,lib,load,ByteArray
from ctypes import c_uint8,c_uint32,POINTER as P,sizeof

class DEVICE_EVENT(DumpableStructure):
 _pack_ = 1
 _fields_ = [
  ('EventNumber',c_uint32),
  ('DateTime',c_uint32),
  ('DeviceID',c_uint32),
  ('DeviceType',c_uint8),
  ('EventCode',c_uint8),
  ('ErrorCode',c_uint8),
  ('DataLen',c_uint8),
  ('EventData',ByteArray(128)),
 ]

print sizeof(DEVICE_EVENT)

class DATETIME(DumpableStructure):
 _pack_ = 1
 _fields_ = [
  ('second',c_uint32,6),
  ('minute',c_uint32,6),
  ('hour',c_uint32,5),
  ('day',c_uint32,5),
  ('month',c_uint32,4),
  ('year',c_uint32,5),
  ('empty',c_uint32,1),
 ]



print sizeof(DATETIME)

proxy_set_mode = load(lib,'proxy_set_mode',(Reader,P(c_uint32)))
proxy_set_time = load(lib,'proxy_set_time',(Reader,P(DATETIME)))
proxy_get_time = load(lib,'proxy_get_time',(Reader,P(DATETIME)))
proxy_get_event = load(lib,'proxy_get_event',(Reader,P(c_uint32),P(DEVICE_EVENT)))
proxy_get_last_event = load(lib,'proxy_get_last_event',(Reader,P(c_uint32)))

reader = Reader()

mode = c_uint32(10)
print 'proxy_set_mode',hex(proxy_set_mode(reader,mode))

dt = DATETIME()
print 'proxy_set_time',hex(proxy_set_time(reader,dt))

print 'proxy_get_time',hex(proxy_get_time(reader,dt))

last_event = c_uint32()
print 'proxy_get_last_event',hex(proxy_get_last_event(reader,last_event))

event = DEVICE_EVENT()
print 'proxy_get_event',hex(proxy_get_event(reader,last_event,event))


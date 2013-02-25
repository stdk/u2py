from ctypes import c_long,c_uint16,memmove,addressof,sizeof
from ctypes import Structure,BigEndianStructure
from datetime import datetime,date
from config import logging
from copy import deepcopy
from time import clock

IO_ERROR           = 0x0E000001

def strParams(params):
 return '( {0} )'.format(', '.join( [str(param) for param in params] ))

def load(library,name,args,res = c_long):
 function = library[name]
 function.argtypes = args
 function.restype = res
 def wrapper(*params):
  begin_clock = clock()
  ret = function(*params)
  time_elapsed = clock() - begin_clock

  logging.debug(' | '.join( ["%6.4f" % (time_elapsed),name,strParams(params),hex(ret)] ))

  if ret == IO_ERROR: #special case for unavailable reader
   #if some function returned IO_ERROR it means its first parameter
   #belongs to Reader class -> should be reopened
   try: params[0].reopen()
   except: pass
   #still, IOError should be raised to notify high level about error
   raise IOError('{0}:{1}'.format(name,strParams(params)))

  return ret
 return wrapper

class Dumpable(object):
 '''
 Represents Dumpable mixin that allows classes to be represented as a json
 serialized string or json itself.
 Uses _fields_ class variable in ctypes format and _dumpable_ class variable
 as a list of fields to be serialized from class.
 to_dict method uses deepcopy by default (use deep=False to disable this).
 '''
 def __str__(self):
  return str(self.to_dict(deep=False))
 __repr__ = __str__

 def _get_attribute_value(self,name,default):
  attribute = getattr(self,name,default)
  if callable(attribute): return attribute()
  return attribute

 def to_dict(self,deep=True):
  names = [field_data[0] for field_data in self._fields_] +\
          self.__class__.__dict__.get('_dumpable_',[])
  result = dict([(name,self._get_attribute_value(name,None)) for name in names if not name.startswith('_')])
  return deepcopy(result) if deep else result

 @classmethod
 def validate(cls,data):
  return data.cast(cls)

class DumpableStructure(Structure,Dumpable):
 pass

class DumpableBigEndianStructure(BigEndianStructure,Dumpable):
 pass

class DATE(Structure):
 _pack_ = 1
 _fields_ = [
    ('year' ,c_uint16,5),
    ('month',c_uint16,4),
    ('day'  ,c_uint16,5),
    ('_'    ,c_uint16,2)
 ]

 def __init__(self,uint16 = None,date = None,**kw):
  if uint16 != None:
   value = c_uint16(uint16)
   memmove(addressof(self),addressof(value),sizeof(self))
  else:
   moment = datetime.now() if not date else date
   self.year,self.month,self.day = moment.year - 2000,moment.month,moment.day
  [setattr(self,key,value) for key,value in kw.iteritems()]

 def to_int(self):
  integer = c_uint16()
  memmove(addressof(integer),addressof(self),sizeof(integer))
  return integer.value

 def to_datetime(self):
  return datetime(year = 2000+self.year,month=self.month,day=self.day)

 def expired(self):
  return date.today() > date(2000 + self.year,self.month,self.day)

 def __str__(self):
  return '%02i/%02i/%02i' % (self.day,self.month,self.year)
 __repr__ = __str__

class TIME(Structure):
 _pack_ = 1
 _fields_ = [
    ('hour'    ,c_uint16,5),
    ('minute'  ,c_uint16,6),
    ('second'  ,c_uint16,5) # seconds are stored divided by 2 due to lack of space
 ]

 def __init__(self,uint16 = None,time = None,**kw):
  if uint16 != None:
   value = c_uint16(uint16)
   memmove(addressof(self),addressof(value),sizeof(self))
  else:
   moment = datetime.now() if not time else time
   self.hour,self.minute,self.second = moment.hour,moment.minute,moment.second/2
  [setattr(self,key,value) for key,value in kw.iteritems()]

 def to_int(self):
  integer = c_uint16()
  memmove(addressof(integer),addressof(self),sizeof(integer))
  return integer.value

 def __str__(self):
  return '%02i:%02i:%02i' % (self.hour,self.minute,self.second*2)
 __repr__ = __str__

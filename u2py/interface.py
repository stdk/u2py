from interface_basis import load,DumpableStructure,DumpableBigEndianStructure
from interface_basis import DATE,TIME,ByteArray,BaseReader,DEBUG
from ctypes import POINTER as P,memmove,byref,cast,sizeof
from ctypes import Structure,c_void_p,c_uint8,c_uint16,c_uint32,c_uint64,c_char
from mfex import *
import config

BLOCK_LENGTH = 16
STANDARD   = 0x4
ULTRALIGHT = 0x44

class Reader(BaseReader):
 def __init__(self,*args,**kw):
  super(Reader,self).__init__(*args,**kw)

 def version(self):
  version = ByteArray(7)()
  if not self.is_open() or reader_get_version(self,version): raise ReaderError()
  return version.cast(c_char*sizeof(version)).raw

 def sn(self):
  sn = ByteArray(8)()
  if not self.is_open() or reader_get_sn(self,sn): raise ReaderError()
  return str(sn)

 def save(self,path = None):
  if path == None: path = self.path
  if not self.is_open() or reader_save(self,path): raise ReaderError()

 def load(self,path = None):
  if path == None: path = self.path
  if not self.is_open() or reader_load(self,path): raise ReaderError()

 def reset_field(self):
  if not self.is_open(): raise ReaderError()
  if reader_field_on(self):
   raise ReaderError()

 def scan(self, sn = None):
  '''
  Resets reader field and returns Card object with information
  about card currently in field.
  Checks for a reader state and tries to open it if closed.
  Giving optional argument sn initiates checked scan procedure:
  it gives WrongCardError when card serial number in fiels != given sn.
  '''
  if not self._is_open: self.open()
  return Card(self,scan = True,prev_sn = sn)

 def __str__(self):
  return '<%s>' % (self.value)
 __repr__ = __str__

SN5 = ByteArray(5)

class SerialNumber(Structure):
 _pack_ = 1
 _fields_ = [('sak',c_uint8),
             ('len',c_uint8),
             ('sn',ByteArray(11))]

 def SN5(self):
  sn = SN5()
  memmove(byref(sn),byref(self.sn,6),sizeof(sn))
  return sn

 def sn7(self):
  sn = c_uint64()
  memmove(byref(sn),byref(self.sn,10-self.len),self.len)
  return sn.value

 def sn8(self):
  return self.sn7() + (self.len << 56)

 def __str__(self):
  return str(self.sn)

class Card(Structure):
 '''
 Card structure should be compatible with underlying library class.
 >>> sizeof(Card)
 16
 '''
 _fields_ = [('sn'   ,SerialNumber),
             ('type' ,c_uint16)]

 def __str__(self):
  return '[{0}:{1}]'.format(self.type,self.sn)
 __repr__ = __str__

 def __init__(self, reader, scan = False, prev_sn = None):
  if DEBUG: print self.__class__.__name__,'__init__'
  self.reader = reader
  if scan: self.scan(prev_sn)

 def scan(self, prev_sn = None):
  self.reader.reset_field()
  if card_scan(self.reader,self): raise CardError()
  if prev_sn != None and self.sn.sn7() != prev_sn: raise WrongCardError()

 def reset(self):
  if card_reset(self.reader,self): raise CardError()

 def auth(self, sector):
  auth_ret = card_sector_auth(self.reader,self,sector)
  if auth_ret: raise SectorReadError(sector.num)

 def sector(self, read = True, **kw):
  sector = Sector(self,**kw)
  self.auth(sector)
  if read: sector.read()
  return sector

 def mfplus_personalize(self):
  ret = card_mfplus_personalize(self.reader,self)
  if ret: raise MFPlusError('Cannot personalize this card')

class Sector(DumpableStructure):
 '''
 Sector structure should be compatible with underlying library class.
 >>> sizeof(Sector)
 51
 >>> 1/0
 Traceback (most recent call last):
 ...
 ZeroDivisionError: integer division or modulo by zero
 '''
 _pack_ = 1
 _fields_ = [
    ('data',ByteArray(BLOCK_LENGTH*3)),
    ('num',c_uint8),
    ('key',c_uint8),
    ('mode',c_uint8) # 0 for static authentication, 1 for dynamic authentication
 ]

 def __init__(self, card, num = 0, key = 0, enc = None,
              mode = None, method = None, blocks = (0,1,2)):
  '''
  Constructor that supports multiple ways of interaction with sector and defines
  its further behaviour.
  The only required arguments are `num` and `key`.
  - `mode` defines method of authentication to this sector.
  It can be either 'static' (default) or 'dynamic'.
  - `method` defines set of I/O function that will read sector data.
  It can be either 'by-blocks' (default, read data from sector block by block)
  or 'full' (read sector data all at once).
  - `enc` defines encryption parameter for data in this sector. Its value depends
  on `method`: when method == 'by-blocks' you should specify a tuple of encryption
  parameters for every(!) block like this: (0xFF,0xFF,0xFF) (default value for this method).
  Using 'full' method requires only one encryption parameter for whole sector
  to be specified and its default value is 0xFF.
  - `blocks` defines a tuple of block indexes that will be used with 'by-blocks'
  method by default when calling I/O function without explicitly specifying blocks affected.
  Default value is (0,1,2). This arguments has no effect with 'full' method.
  '''
  if DEBUG: print 'Sector.__init__',num

  self.card = card
  self.num = num
  self.key = key

  if not mode: mode = 'static'
  self.set_mode(mode)

  if not method: method = 'by-blocks'
  self.__class__ = { 'full' : FullSector, 'by-blocks' : ByBlockSector}[method]

  self.blocks = blocks

  if not enc: enc = { 'full' : 0xFF, 'by-blocks' : (0xFF,0xFF,0xFF) }[method]
  self.enc = enc

 def set_mode(self,mode):
  self.mode = {'static': 0, 'dynamic' : 1}[mode]

 def write_block(self,i,enc = None):
  if not enc: enc = self.enc[i] if isinstance(self,ByBlockSector) else self.enc
  if card_block_write(self.card.reader,self,i,enc): raise SectorWriteError(self.num,i)

 def set_trailer(self,key,mode=None):
  if not mode: mode = 'static'
  self.set_mode(mode)
  self.key = key
  if self.mode == 1:
   if card_sector_set_trailer_dynamic(self.card.reader,self,self.card): raise SectorWriteError(self.num,3)
  else:
   if card_sector_set_trailer(self.card.reader,self): raise SectorWriteError(self.num,3)

class FullSector(Sector):
 def read(self):
  if card_sector_read(self.card.reader,self,self.enc): raise SectorReadError(self.num)

 def write(self,blocks = None):
  if blocks: return [self.write_block(block,self.enc) for block in blocks]
  if card_sector_write(self.card.reader,self,self.enc): raise SectorWriteError(self.num)

class ByBlockSector(Sector):
 def read(self,blocks = None):
  if not blocks: blocks = self.blocks
  for b in blocks:
   if card_block_read(self.card.reader,self,b,self.enc[b]): raise SectorReadError(self.num,b)

 def write(self,blocks = None):
  if not blocks: blocks = self.blocks
  for b in blocks:
   if card_block_write(self.card.reader,self,b,self.enc[b]): raise SectorWriteError(self.num,b)

reader_field_on         = load('reader_field_on'           ,(Reader,))
reader_field_off        = load('reader_field_off'          ,(Reader,))

reader_get_sn           = load('reader_get_sn'             ,(Reader,P(ByteArray(8))))
reader_get_version      = load('reader_get_version'        ,(Reader,P(ByteArray(7))))

reader_save             = load('reader_save'               ,(Reader,P(c_char)))
reader_load             = load('reader_load'               ,(Reader,P(c_char)))

card_mfplus_personalize = load('card_mfplus_personalize'   ,(Reader,P(Card)))
card_scan               = load('card_scan'                 ,(Reader,P(Card),))
card_reset              = load('card_reset'                ,(Reader,P(Card),))
card_sector_auth        = load('card_sector_auth'          ,(Reader,P(Card),P(Sector),))
card_block_read         = load('card_block_read'           ,(Reader,P(Sector),c_uint8,c_uint8,))
card_block_write        = load('card_block_write'          ,(Reader,P(Sector),c_uint8,c_uint8,))
card_sector_read        = load('card_sector_read'          ,(Reader,P(Sector),c_uint8,))
card_sector_write       = load('card_sector_write'         ,(Reader,P(Sector),c_uint8,))
card_sector_set_trailer = load('card_sector_set_trailer'   ,(Reader,P(Sector)))
card_sector_set_trailer_dynamic = load('card_sector_set_trailer_dynamic'   ,(Reader,P(Sector),P(Card)))

def random_data(size,a=0,b=0xFF):
 from random import randint
 data = (c_uint8*size)()
 [data.__setitem__(i,int(randint(a,b))) for i in xrange(size)]
 return data

def test_bytestaffing():
 '''
 Function returns an array of test indexes that failed.
 All bytestaffing tests should pass without errors
 >>> test_bytestaffing()
 []
 '''
 from time import time
 test = load('bytestaffing_test',())
 a = time()
 test_data = [random_data(1000) for i in xrange(100)]
 b = time()
 tests = [ test(data,sizeof(data)) for data in test_data ]
 c = time()
 return [i for i in tests if i]

if __name__ == '__main__':
 import doctest
 doctest.testmod()

 reader = Reader()

 print reader.sn()
 print reader.version()

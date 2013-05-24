CARD_ERROR         = 0xCE0000C0
READER_ERROR       = 0xCE0000FA
SECTOR_READ_ERROR  = 0xCE00005A
SECTOR_WRITE_ERROR = 0xCE00005B
CRC_ERROR          = 0xCE0000CF
STATUS_ERROR       = 0xCE00005F
DATA_ERROR         = 0xCE0000DF
TIME_ERROR         = 0xCE00007F
VALUE_ERROR        = 0xCC000001

class ReaderError(Exception):
 def __str__(self):
  return 'Requested reader is not available'

class CardError(Exception):
 def __str__(self):
  return 'There is no card in reader field'

class MFPlusError(Exception):
 def __init__(self,message):
  self.message = message
 def __str__(self):
  return self.message

class WrongCardError(Exception):
 def __str__(self):
  return 'Card in reader field is not the requested one'

class StoplistError(Exception):
 def __str__(self):
  return 'This card is stoplisted'

class ValueError(Exception):
 def __init__(self,message):
  self.message = message
 def __str__(self):
  return self.message

class MFEx(Exception):
 def __init__(self,code,sector=0,block=0):
  self.code = code
  self.sector = sector
  self.block = block

 def getCode(self):
  return self.code + (self.sector << 16) + (self.block << 8)

 def __str__(self):
  return '%08X' % self.getCode()

 def to_dict(self):
  return {
   'code'  : self.getCode(),
   'type'  : unicode(self.__class__.__name__),
   'hex'   : str(self),
   'sector': self.sector,
   'block' : self.block
  }

class SectorReadError(MFEx):
 def __init__(self,sector=0,block=0):
  MFEx.__init__(self,SECTOR_READ_ERROR,sector,block)

class SectorWriteError(MFEx):
 def __init__(self,sector=0,block=0):
  MFEx.__init__(self,SECTOR_WRITE_ERROR,sector,block)

class CRCError(MFEx):
 def __init__(self,sector=0,block=0):
  MFEx.__init__(self,CRC_ERROR,sector,block)\

class StatusError(MFEx):
 def __init__(self,sector=0,block=0):
  MFEx.__init__(self,STATUS_ERROR,sector,block)

class DataError(MFEx):
 def __init__(self,sector=0,block=0):
  MFEx.__init__(self,DATA_ERROR,sector,block)

class TimeError(Exception):
 def __init__(self,message):
  super(TimeError,self).__init__(message)

class UnsupportedRefillContract(Exception):
 def __str__(self):
  return 'Contract refill is not supported'
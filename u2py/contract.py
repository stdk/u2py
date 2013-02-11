from interface import DumpableStructure,ByteArray,Reader
from mfex import *
from ctypes import Structure,memmove,addressof,sizeof,cast,pointer as p,POINTER as P

class DYNAMIC_A(DumpableStructure):
 _fields_ = [('b1',ByteArray(16)),
             ('b2',ByteArray(16))]

 def __init__(self,cls):
  dynamic = cast(p(cls()),P(ByteArray(sizeof(cls)))).contents
  self.b1,self.b2 = dynamic,dynamic

 def commit(self,data,low_endian=1):
  '''
  This functions finalizes contents of dynamic contract part in memory.
  `data` argument should contain single valid block (ByteArray(16) or any
  other size-compatible ctypes type).
  This data will then be copied to block1, crc16 summ will be calculated in-place
  and block1 will be copied to block2.
  '''
  dst1,dst2,src = addressof(self.b1),addressof(self.b2),addressof(data)
  size = sizeof(self.b1)
  memmove(dst1,src,min(size,sizeof(data)))
  self.b1.crc16_calc(low_endian=low_endian)
  memmove(dst2,dst1,size)

 @classmethod
 def validate(cls,sector,dynamic_class):
  '''
  Unlike other validate methods, this one requires two arguments instead of one:
  both `sector` and `dynamic data` (instead of jsut simple ByteArray)
  are required for successfull check and restoration of possible failed blocks.
  When there is no way to restore dynamic data for given dynamic_class this function
  throws CRCError.
  To make fail block restore operation successfull, sector should be authenticated,
  i.e. there should be no other auth operations on this card before validating.
  Returns tuple of DYNAMIC_A object and dynamic_class object retrieved from sector data.
  '''
  proxy = sector.data.cast(cls)
  try:
   fail_block = proxy.restore(dynamic_class)
   if fail_block: sector.write_block(fail_block)
  except CRCError: raise CRCError(sector.num)
  return proxy,proxy.b1.cast(dynamic_class)

 def __str__(self):
  return '{0}+{1}'.format(self.b1,self.b2)

 def restore(self,dynamic_class):
  '''
  Return value: index of restored block or None, if there is no need to restore anything.

  This functions tries to restore dynamic contract part with given business-logic:
  1. Validate block1 and block2 of dynamic part and find out its status (correct,incorrect).
  2. If there is no correct blocks, raise CRCError.
  3. If both blocks are correct and their contents are the same, return None.
  4. If both blocks are correct, they should be compared with their __cmp__ to decide
     which of them is better for the passenger (currently, block with lesser transaction number is preferable).
     Preferable block is decided as correct and another one as incorrect.
  5. If there is only one correct block (from the very beginning or after previous step),
     its contents are copied over incorrect block and index of incorrect block is returned.

  Higher level calling this function should decide an action to perform after catching an exception of
  receiving index of incorrect block to write. Since contents of incorrect block should be same
  with correct block, only `Sector.write_block call` is required. However, upon receiving this information
  another course of action can be taken, exempli gratia discard current sector data and try to read it with another
  key or encryption configuration.
  '''
  def get(block):
   try: return dynamic_class.validate(block)
   except MFEx as e:
    print e.__class__.__name__,e
    return None

  a, b = get(self.b1), get(self.b2)
  #print not not a, not not b

  if not a and not b:
   raise CRCError()

  if a and b and self.b1 == self.b2:
   return None

  if a and (not b or a < b):
   ret,src,dst = 2,self.b1,self.b2
  else:
   ret,src,dst = 1,self.b2,self.b1

  src.copy(dst = dst)
  return ret

class CONTRACT_A(DumpableStructure):
 _fields_ =[('static_block',ByteArray(16)),
            ('dynamic_part',DYNAMIC_A)]

 def __init__(self,static_class,dynamic_class):
  static = cast(p(static_class()),P(ByteArray(sizeof(static_class)))).contents
  self.static_block = static
  self.dynamic_part.__init__(dynamic_class)

 def commit(self,low_endian=1):
  self.dynamic_part.commit(self.dynamic,low_endian)

 @classmethod
 def validate(cls,sector,static_class,dynamic_class):
  contract = sector.data.cast(cls)

  try:
   contract.static = static_class.validate(contract.static_block)
  except CRCError as e: raise CRCError(sector.num,1)
  except MFEx as e:
   e.data1,e.data2 = sector.num,1
   raise

  try:
   fail_block = contract.dynamic_part.restore(dynamic_class)
   if fail_block: sector.write_block(fail_block)
  except CRCError: raise CRCError(sector.num)

  contract.dynamic = contract.dynamic_part.b1.cast(dynamic_class)

  return contract
from interface_basis import DumpableStructure,ByteArray
from ctypes import Structure,memmove,sizeof,byref
from mfex import *
import logging


class DYNAMIC_A(DumpableStructure):
 _fields_ = [('b1',ByteArray(16)),
             ('b2',ByteArray(16))]

 def __str__(self):
  return '{0}+{1}'.format(self.b1,self.b2)

 def __init__(self, cls):
  self.dynamic_class = cls
  data = ByteArray(cls())
  self.b1,self.b2 = data,data

 def __enter__(self):
  return self.b1.cast(self.dynamic_class)

 def __exit__(self,*exc_info):
  self.b1.cast(self.dynamic_class).update_checksum()
  self.b2 = self.b1

 def commit(self,data,low_endian=1):
  '''
  This functions finalizes contents of dynamic contract part in memory.
  `data` argument should contain single valid block (ByteArray(16) or any
  other size-compatible ctypes type).
  This data will then be copied to block1, checksum will be calculated in-place
  and block1 will be copied to block2.
  Object being commited should be able to calculate its own checksum
  via |update_checksum| method.
  '''
  data.update_checksum()
  self.b1 = ByteArray(data)
  self.b2 = self.b1

 @classmethod
 def validate(cls, data, dynamic_class, callback):
  '''
   Return value: (DYNAMIC_A instance, dynamic_class instance from given data)
   Possible exceptions: CRCError when there is no way to restore dynamic data.

   Unlike other validate methods, this one requires at least three arguments
  instead of one: `data`, `dynamic class` and `callback` are required for
  successfull check and restoration of possible failed blocks.
   Unlike first two arguments, `callback` requires some clarification:
  this parameter should contain callable that accepts integer number (0 or 1),
  treats this number as index of failed block in DYNAMIC_A reference system
  and reacts accordingly. This |callback| will only be called in case failed block
  is actually present within data.
   Usually, callback should contain something like
                  |sector.write_block(fail_block + block_diff)|,
  where block_diff if a difference between sector and DYNAMIC_A reference points.
   To make fail block restore operation successfull, it is necessary to be authenticated
  to a sector in question. Thus, caller must either ensure absence of another
  authentication operations with card before DYNAMIC_A validation or manually
  perform authentication whenever required.
  '''
  proxy = data.cast(cls)
  dynamic_class_instance = proxy.restore(dynamic_class, callback)
  return proxy, dynamic_class_instance

 def restore(self, dynamic_class, callback):
  '''
  Return value: dynamic_class instance from its own data
  For everything else see DYNAMIC_A.validate.
  This is instanced version of the same functionality.
  '''
  self.dynamic_class = dynamic_class
  fail_block = self.amend_fail_block(dynamic_class)
  if fail_block != None:
   logging.debug('restoring fail block[%i]' % (fail_block,))
   callback(fail_block)
  return self.b1.cast(dynamic_class)

 def amend_fail_block(self,dynamic_class):
  '''
  Return value: index of in-memory restored block or None, if everything is ok.

  This functions tries to restore dynamic contract part in memory with given business-logic:
  1. Validate block1 and block2 of dynamic part and find out its status (correct,incorrect).
  2. If there are no correct blocks, raise CRCError.
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
    return None

  a, b = get(self.b1), get(self.b2)

  if not a and not b:
   raise CRCError()

  if a and b and self.b1 == self.b2:
   return None

  if a and (not b or a < b):
   ret,src,dst = 1,self.b1,self.b2
  else:
   ret,src,dst = 0,self.b2,self.b1

  src.copy(dst = dst)
  return ret

class CONTRACT_A(DumpableStructure):
 _fields_ =[('static_block',ByteArray(16)),
            ('dynamic_part',DYNAMIC_A)]

 def __init__(self,static_class,dynamic_class):
  self.static_block = ByteArray(static_class())
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

  def restore_callback(fail_block):
   print 'CONTRACT_A restore_callback sector[%i] block[%i]' %(sector.num,fail_block + 1)
   sector.write_block(fail_block + 1)

  try:
   contract.dynamic = contract.dynamic_part.restore(dynamic_class,
                                                    callback = restore_callback)
  except CRCError:
   raise CRCError(sector.num,2)

  return contract
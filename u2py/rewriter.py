from interface import load,Reader,ByteArray
from interface import reader_get_sn,reader_get_version
from ctypes import c_char_p,c_char,c_uint32
import time
from multiprocessing.pool import ThreadPool
from threading import Event
from PyQt4 import QtGui,QtCore,uic
from PyQt4.QtGui import QFileDialog,QMainWindow,QStandardItemModel,QStandardItem, QApplication, QCursor
from PyQt4.QtCore import pyqtSignal,Qt
from pkg_resources import resource_stream

reader_update_start      = load('reader_update_start'       ,(Reader,))
reader_sync              = load('reader_sync'               ,(Reader,))
reader_send_package      = load('reader_send_package'       ,(Reader,c_char_p,c_uint32))

class Widget(QMainWindow):
 progressChanged = pyqtSignal(int)
 statusChanged = pyqtSignal(str)
 writeCompleted = pyqtSignal()

 def __init__(self,parent=None):
  QMainWindow.__init__(self,parent)
  uiClass, qtBaseClass = uic.loadUiType(resource_stream(__name__,'rewriter.ui'))
  self.ui = uiClass()
  self.ui.setupUi(self)

  self.init_baud()

  self.thread_pool = ThreadPool(1)
  self.reader = None
  self.firmware = None
  self.stop_event = Event()

  self.ui.btOpen.clicked.connect(self.open_port)
  self.ui.btClose.clicked.connect(self.close_port)
  self.ui.btSelect.clicked.connect(self.select_firmware)
  self.ui.btStart.clicked.connect(self.start)
  self.ui.btStop.clicked.connect(self.stop_event.set)

  self.progressChanged.connect(self.ui.progressbar.setValue)
  self.writeCompleted.connect(self.on_write_completed)
  self.statusChanged.connect(self.on_status_changed)

 def init_baud(self):
  model = QStandardItemModel()
  model.insertRow(0,QStandardItem('38400'))
  model.insertRow(1,QStandardItem('500000'))
  self.ui.baud.setModel(model)

 def set_buttons_enabled(self,eOpen=None,eClose=None,eStart=None,eStop=None,eSelect=None):
  if eOpen != None:  self.ui.btOpen.setEnabled(eOpen)
  if eClose != None: self.ui.btClose.setEnabled(eClose)
  if eStart != None: self.ui.btStart.setEnabled(not not self.firmware and eStart)
  if eStop != None: self.ui.btStop.setEnabled(eStop)
  if eSelect != None: self.ui.btSelect.setEnabled(eSelect)

 def open_port(self):
  path = '\\\\.\\COM%i' % self.ui.port.value()
  baud = int(self.ui.baud.currentText())

  #Blockwise and bytewise implementations have issues with default comm timeouts
  #that can lead to spontaneous host computer reboot. Using asio instead.
  self.reader = Reader(path = path, baud = baud, explicit_error = True)

  if not self.reader.is_open():
   return self.ui.statusbar.showMessage('Cannot open port')

  QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
  try:
   sn = ByteArray(8)()
   version = ByteArray(7)()
   ret = reader_get_sn(self.reader,sn),reader_get_version(self.reader,version)
   self.setWindowTitle('Reader %s:%s' % (sn,version.cast(c_char*7).raw))
   self.ui.statusbar.showMessage('Port successfully opened')
  except IOError:
   self.ui.statusbar.showMessage('There is no reader at the other side')
  finally:
   QApplication.restoreOverrideCursor()

  self.set_buttons_enabled(False,True,True)
  self.ui.port.setEnabled(False)
  self.ui.baud.setEnabled(False)

 def close_port(self):
  self.reader.close()
  del self.reader
  self.set_buttons_enabled(True,False,False)
  self.ui.port.setEnabled(True)
  self.ui.baud.setEnabled(True)
  self.ui.statusbar.clearMessage()
  self.setWindowTitle('')

 def get_open_filename(self):
  return unicode(QFileDialog.getOpenFileName(self, u"Select firmware",u"",u"Encrypted firmware (*.enc)"))

 def select_firmware(self):
  filename = self.get_open_filename()
  if not filename: return
  self.ui.firmware.setText(filename)
  self.firmware = filename
  self.set_buttons_enabled(eStart = not not self.reader)

 def start(self):
  self.ui.statusbar.showMessage('Start firmware write... ')
  self.stop_event.clear()
  args = (self.reader,self.firmware)
  self.async_result = self.thread_pool.apply_async(self.write_wrapper,args)

  self.ui.progressbar.setValue(0)
  self.set_buttons_enabled(False,False,False,True,False)

 def on_write_completed(self):
  self.set_buttons_enabled(False,True,True,False,True)
  try:
   self.async_result.get()
   self.async_result = None
   self.ui.statusbar.showMessage('Firmware write completed')
  except Exception as e:
   current_message = self.ui.statusbar.currentMessage()
   self.ui.statusbar.showMessage(u'%s -> [%s]:%s' % (current_message,e.__class__.__name__,e))

 def on_status_changed(self,message):
  self.ui.statusbar.showMessage(message)

 def write_wrapper(self,reader,filename):
  try:
   self.write(reader,filename)
  finally:
   self.writeCompleted.emit()

 def write(self,reader,filename):
  firmware = open(filename).read().decode("hex")
  full_size = len(firmware)

  self.statusChanged.emit('Sending update start command...')
  reader_update_start(reader)
  self.statusChanged.emit('Update start success. Waiting for sync...')
  time.sleep(0.5)
  reader_sync(reader)
  self.statusChanged.emit('Writing firmware...')

  while len(firmware):
   if self.stop_event.is_set(): raise Exception('Firmware write cancelled.')

   size = (ord(firmware[0]) << 8) + ord(firmware[1]) + 2
   ret = reader_send_package(reader,firmware[2:size],size-4)
   if ret:
    raise Exception('reader_send_package returned %i' % (ret,))
   progress = 100 - 100 * len(firmware) / full_size
   self.progressChanged.emit(progress)
   firmware = firmware[size:]

def app():
 import sys
 from PyQt4.QtGui import QApplication
 app = QApplication(sys.argv)
 widget = Widget()
 widget.show()
 sys.exit(app.exec_())

if __name__ == '__main__':
 app()

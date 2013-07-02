import os
import sys
import win32serviceutil
import win32service
import win32event
import win32evtlogutil
import servicemanager

class logger(object):
 def __init__(self,out):
  self.out = out
 def write(self,message):
  if 'Traceback' in message:
   self.out('\n' + message)

class ServiceLauncher(win32serviceutil.ServiceFramework):
 _svc_name_ = 'U2 Service'
 _scv_display_name_ ='U2 Service'

 def __init__(self, args):
  win32serviceutil.ServiceFramework.__init__(self, args)

  sys.stderr = logger(servicemanager.LogInfoMsg)
  os.chdir(os.path.dirname(sys.executable))

 def SvcStop(self):
  self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
  self.server.stop()

 def SvcDoRun(self):
  exec(open('config.py').read())

  from webapi.server import make_server
  self.server = make_server()
  self.server.serve_forever()
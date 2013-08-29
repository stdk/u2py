import os
import sys
import time
import win32serviceutil
import win32service
import win32event
import win32evtlogutil
import win32console
import servicemanager

# Give the multiprocessing module a python interpreter to run
import multiprocessing
executable = os.path.join(os.path.dirname(sys.executable), 'u2.exe')
multiprocessing.set_executable(executable)
del executable

BASE_PROCESS_WAIT_TIME = 3

class logger(object):
 def __init__(self,out):
  self.out = out
 def write(self,message):
  if 'Traceback' in message:
   self.out('\n' + message)

class ServiceLauncher(win32serviceutil.ServiceFramework):
 _svc_name_ = 'U2 Service'
 _svc_display_name_ ='U2 Service'

 def __init__(self, args):
  win32serviceutil.ServiceFramework.__init__(self, args)

  l = logger(servicemanager.LogInfoMsg)
  sys.stdout = l
  sys.stderr = l
  os.chdir(os.path.dirname(sys.executable))

  exec(open('config.py').read())
  import webapi.config
  self.mode = webapi.config.service_mode

  servicemanager.LogInfoMsg('\nService mode = %s' % (self.mode))

  if self.mode == 'process':
   # CREATE_NEW_PROCESS_GROUP with win32console.AllocConsole() are required for send_signal(signal.CTRL_BREAK_EVENT).
   # Both signal sender and receiver should have console allocated.
   win32console.AllocConsole()

 def SvcStop(self):
  self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
  if self.mode == 'process':
   import signal
   self.server_process.send_signal(signal.CTRL_BREAK_EVENT)
   time.sleep(BASE_PROCESS_WAIT_TIME)
   if self.server_process.poll() == None:
    servicemanager.LogInfoMsg('\nMain process still running despite the break signal.')
    self.server_process.kill()
  else:
   self.server.stop()

 def SvcDoRun(self):
  if self.mode == 'process':
   from subprocess import Popen,CREATE_NEW_PROCESS_GROUP
   self.server_process = Popen(['u2.exe','api'],creationflags = CREATE_NEW_PROCESS_GROUP)
   self.server_process.wait()
  else:
   exec(open('config.py').read())

   from webapi.server import make_server
   self.server = make_server()
   self.server.serve_forever()

if __name__ == '__main__':
 multiprocessing.freeze_support()

 # Pass the command line to the service utility library.
 # This can handle start, stop, install, remove and other commands.
 win32serviceutil.HandleCommandLine(ServiceLauncher)
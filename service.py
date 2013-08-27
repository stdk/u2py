import os
import sys
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
  
  # CREATE_NEW_PROCESS_GROUP with win32console.AllocConsole() are required for send_signal(signal.CTRL_BREAK_EVENT)
  win32console.AllocConsole()

 def SvcStop(self):
  import signal 

  self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
  self.server_process.send_signal(signal.CTRL_BREAK_EVENT)
  #os.kill(self.server_process.pid, signal.CTRL_BREAK_EVENT)
  #self.server.stop()

 def SvcDoRun(self):
  from subprocess import Popen,CREATE_NEW_PROCESS_GROUP
  
  self.server_process = Popen(['u2.exe','api'],creationflags = CREATE_NEW_PROCESS_GROUP)
  self.server_process.wait()
 
  #exec(open('config.py').read())

  #from webapi.server import make_server
  #self.server = make_server()
  #self.server.serve_forever()

if __name__ == '__main__':
 multiprocessing.freeze_support()

 # Pass the command line to the service utility library.
 # This can handle start, stop, install, remove and other commands.
 win32serviceutil.HandleCommandLine(ServiceLauncher)
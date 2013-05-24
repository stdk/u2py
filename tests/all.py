import glob
import unittest
from threading import Thread,Event
from subprocess import Popen,PIPE,CREATE_NEW_PROCESS_GROUP

def test_files(pathname):
 test_file_strings = glob.glob(pathname)
 module_strings = [str[0:len(str)-3] for str in test_file_strings]
 suites = [unittest.defaultTestLoader.loadTestsFromName(str) for str
           in module_strings]
 testSuite = unittest.TestSuite(suites)
 text_runner = unittest.TextTestRunner(verbosity=2).run(testSuite)

class U2(Thread):
 def run(self):
  self.terminate_event = Event()
  self.pipe = Popen(['c:\\python27\\python.exe','u2.py','api'],cwd = '..\\.')
  self.terminate_event.wait()
  self.pipe.terminate()

 def terminate(self):
  self.terminate_event.set()

if __name__ == '__main__':
 test_files('test_*.py')
 u2 = U2()
 u2.start()
 test_files('service_test_*.py')
 u2.terminate()

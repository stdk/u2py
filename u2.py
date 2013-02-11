import multiprocessing
from multiprocessing import Process
from sys import argv

def api():
 from webapi import server
 server.run()

def adbk():
 from adbk import adbk
 adbk.run()

def rewriter():
 from u2py import rewriter
 rewriter.app()

if __name__ == '__main__':
 multiprocessing.freeze_support()

 exec(open('config.py').read())

 def default():
  print 'No options specified. Available: api, adbk.'

 modes = { 'adbk' : adbk, 'api' : api }
 modes.get(len(argv) > 1 and argv[1] or None,rewriter)()


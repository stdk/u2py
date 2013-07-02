def api():
 from webapi.server import make_server
 make_server().serve_forever()

def adbk():
 from adbk import adbk
 adbk.run()

def rewriter():
 from u2py import rewriter
 rewriter.app()

if __name__ == '__main__':
 exec(open('config.py').read())

 from sys import argv

 def default():
  print 'No options specified. Available: api, adbk.'

 modes = { 'adbk' : adbk, 'api' : api }
 modes.get(len(argv) > 1 and argv[1] or None,rewriter)()

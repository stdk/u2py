from distutils.core import setup
import py2exe, sys

from u2py.config import VERSION
from datetime import datetime

sys.argv.append('py2exe')

base_opts = [
	("icon_resources", [(1, "icon.ico")]),
	("version", '.'.join(str(i) for i in VERSION)),
	("company_name", "Card Systems"),
	("name", 'u2py' + ' (' + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ')')
]

setup(
 name = "u2",
 description = "u2 service",
 version = '.'.join(str(i) for i in VERSION),
 console = [ dict([( 'script', "u2.py")] + base_opts) ],
 service = [ dict([ ('modules', ["service"]), ('cmdline', 'pywin32') ] + base_opts)],
 #zipfile = 1,
 data_files = [
	  ('.',['u2.dll','config.py','u2.doc']),
	  ('templates',['webapi/templates/index.html']),
	  ('static',['webapi/static/jquery-1.8.0.min.js','u2py/rewriter.ui'])
	],
 options = {
  'py2exe':{
   'packages':'encodings',
   "includes":"win32com,win32service,win32serviceutil,win32event,servicemanager,greenlet,sip",
   'excludes': [ 'config','email','distutils','tcl','Tkconstants', 'Tkinter', 'pydoc', 'doctest', 'test','cherrypy'],
   'dll_excludes': ['tcl84.dll','tk84.dll','MSVCP90.dll'],
   'optimize': '2',
   'bundle_files' : 2,
   'compressed' : True
  },
 },
)
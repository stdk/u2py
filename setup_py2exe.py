from distutils.core import setup
import py2exe, sys, os
from py2exe.build_exe import py2exe as builder
import glob

from u2py.config import VERSION
from datetime import datetime

sys.argv.append('py2exe')

base_opts = [
	("icon_resources", [(1, "icon.ico")]),
	("version", '.'.join(str(i) for i in VERSION)),
	("company_name", "Card Systems"),
	("name", 'u2py' + ' (' + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ')')
]

class PackageDataCollector(builder):
 def __init__(self,distribution):
  self.package_data = distribution.package_data
  builder.__init__(self,distribution)

 def copy_extensions(self, extensions):
  builder.copy_extensions(self,extensions)

  for package,masks in self.package_data.iteritems():
   destination = os.path.join(self.collect_dir,package)
   for mask in masks:
    for filename in glob.glob(os.path.join(package,mask)):
     reldir = os.path.dirname(os.path.relpath(filename,package))
     copy_dir = os.path.join(destination,reldir)
     if not os.path.exists(copy_dir):
      self.mkpath(copy_dir)

     self.copy_file(filename, copy_dir)
     self.compiled_files.append(filename)


setup(
 cmdclass = { 'py2exe': PackageDataCollector },
 name = "u2",
 description = "u2 service",
 version = '.'.join(str(i) for i in VERSION),
 console = [ dict([( 'script', "u2.py")] + base_opts) ],
 service = [ dict([ ('modules', ["service"]), ('cmdline', 'pywin32') ] + base_opts)],
 #zipfile = 1,
 data_files = [
 	  ('.',['u2.dll','config.py','u2.doc']),
 ],
 package_data = {
       'webapi': ['static/*', 'templates/*'],
       'u2py': ['rewriter.ui'],
    },
 options = {
  'py2exe':{
   'packages':'encodings',
   "includes":"win32com,win32service,win32serviceutil,win32event,servicemanager,greenlet,sip,distutils",
   'excludes': [ 'config','email','distutils','tcl','Tkconstants', 'Tkinter', 'pydoc', 'doctest', 'test','cherrypy'],
   'dll_excludes': ['tcl84.dll','tk84.dll','MSVCP90.dll'],
   'optimize': '2',
   'bundle_files' : 2,
   'compressed' : True
  },
 },
)
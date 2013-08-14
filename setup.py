from distutils.sysconfig import get_python_lib
from distutils.core import setup
from u2py import __version__
from sys import platform
win32 = platform == 'win32'

data_files = [
 (get_python_lib(prefix = None if win32 else '/usr/local'),
  ['u2.dll' if win32 else 'libu2.so'])
]

setup(
    name='u2py',
    version = __version__ + '.0',
    author='feanor',
    author_email='std.feanor@gmail.com',
    packages=['u2py','webapi','adbk'],
    scripts=['u2.py'],
    url='https://github.com/stdk/u2py',
    license='LICENSE.txt',
    description='u2py',
    long_description=open('README.txt').read(),
	data_files = data_files,
    package_data = {
       'webapi': ['static/*', 'templates/*'],
       'u2py': ['rewriter.ui'],
    },
    install_requires=[

    ]
)
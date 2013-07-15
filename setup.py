from distutils.core import setup

setup(
    name='u2py',
    version='1.6.2',
    author='feanor',
    author_email='std.feanor@gmail.com',
    packages=['u2py','webapi','adbk'],
    scripts=['u2.py'],
    url='https://github.com/stdk/u2py',
    license='LICENSE.txt',
    description='u2py',
    long_description=open('README.txt').read(),
    install_requires=[
        
    ],
)
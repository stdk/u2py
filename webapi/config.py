import os

host = '127.0.0.1'
port = 1000

webapi_folder = os.path.dirname(__file__).decode('cp1251')
static_folder = os.path.join(webapi_folder,'static')
templates_folder = os.path.join(webapi_folder,u'templates')

notifier_poll_timeout = 0.5

read_api_requires_server = False
write_api_requires_server = True

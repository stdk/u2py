import os

host = '127.0.0.1'
port = 1000

webapi_folder = os.path.dirname(__file__).decode('cp1251')
base_folder = os.path.join(webapi_folder,'..')
static_folder = os.path.join(base_folder,'static')
templates_folder = os.path.join(base_folder,u'templates')

notifier_poll_timeout = 0.5
error_with_traceback = True

read_api_requires_server = False
write_api_requires_server = True

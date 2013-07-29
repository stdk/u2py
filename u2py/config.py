import os
from sys import platform

if platform == 'win32': from time import clock as time
if platform == 'linux2': from time import time

lib_base_filename = 'u2.dll' if platform == 'win32'else 'libu2.so'
lib_filename      = os.path.join(os.path.dirname(__file__),'..',lib_base_filename)
db_filename       = 'db.db3'

reader_path       = [
    {'path': '\\\\.\\COM1', 'baud': 38400, 'impl':'asio-mt' }
]

max_journeys = 50
journey_cost = 200

term_full_cost    = 9500
term_half_cost    = 4800
hall_id           = 100


try:
 if platform != 'linux2': raise #for now linux ip detection has been disabled
 import socket
 hall_device_id   = int(socket.gethostbyname(socket.gethostname()).split('.')[-1]) - 10
except:
 hall_device_id   = 0xFF


device_type       = 2

password          = '123456'

cash_card_sn      = 0
cash_card_aspp    = '0' * 16

reopen_on_io_error = True


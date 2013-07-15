import os

VERSION = 1,6,2

lib_filename      = '../u2.dll'
db_filename       = 'db.db3'

reader_path       = [
    {'path': '\\\\.\\COM1', 'baud': 38400, 'impl':'asio-mt' }
]

max_journeys = 50
journey_cost = 200

term_full_cost    = 9500
term_half_cost    = 4800
hall_id           = 100

base_folder = os.path.dirname(__file__).decode('cp1251')
rewriter_ui_path = os.path.join(base_folder,'rewriter.ui')

import socket
try:
 hall_device_id   = int(socket.gethostbyname(socket.gethostname()).split('.')[-1]) - 10
except:
 hall_device_id   = 0xFF

device_type       = 2

password          = '123456'

cash_card_sn      = 0
cash_card_aspp    = '0' * 16

reopen_on_io_error = True


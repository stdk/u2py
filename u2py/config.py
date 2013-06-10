import logging
import logging.config

VERSION = 1,5,11

lib_filename      = '../u2.dll'
db_filename       = 'db.db3'

reader_path       = [
    {'path': '\\\\.\\COM2', 'baud': 38400, 'impl':'asio' }
]

max_journeys = 50
journey_cost = 200

term_full_cost    = 9500
term_half_cost    = 4800
hall_id           = 100

rewriter_ui_path = 'rewriter.ui'

import socket
try:
 hall_device_id   = int(socket.gethostbyname(socket.gethostname()).split('.')[-1]) - 10
except:
 hall_device_id   = 0xFF

device_type       = 2

password          = '123456'

cash_card_sn      = 0
cash_card_aspp    = '0' * 16


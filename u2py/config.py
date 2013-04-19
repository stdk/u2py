import logging
import logging.config

logging.config.dictConfig({
 'version': 1,    # Configuration schema in use; must be 1 for now
 'formatters': {
     'standard': {
         'format': ('%(asctime)s '
                    '%(levelname)-8s %(message)s')}},
 'handlers': {'u2': { 'backupCount': 10,
                       'class': 'logging.handlers.RotatingFileHandler',
                       'filename': 'u2.log',
                       'formatter': 'standard',
                       'level': 'DEBUG',
                       'maxBytes': 10000000 }
             },
 # Specify properties of the root logger
 'root': { 'level': 'DEBUG', 'handlers': ['u2'] },
})

reader_path       = [
    {'path': '\\\\.\\COM2', 'baud': 38400, 'impl':'asio' }
]
lib_filename      = '../u2.dll'
db_filename       = 'db.db3'
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
cash_card_aspp    = '0000000000000000'


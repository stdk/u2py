import webapi.config

webapi.config.host                      = '127.0.0.1'
webapi.config.port                      = 1000
webapi.config.read_api_requires_server  = False
webapi.config.write_api_requires_server = False

import u2py.config
u2py.config.reader_path       = [
    {'path': '\\\\.\\COM2', 'baud': 38400, 'impl':'blockwise' }
]
u2py.config.rewriter_ui_path = 'u2py/rewriter.ui'
u2py.config.lib_filename    = './u2.dll'
u2py.config.db_filename     = 'db.db3'
u2py.config.hall_id         = 100
u2py.config.term_full_cost  = 9500
u2py.config.term_half_cost  = 4800


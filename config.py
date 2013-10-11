# Настройки вебсервера, обслуживающего API
import webapi.config

# Хост и порт вебсервера
webapi.config.host = '0.0.0.0'
webapi.config.port = 1000

# Настройки требовательности команд API к наличию сервера.
# К командам чтения относятся: /api/scan и /api/term/available .
# Все остальные команды являюися командами записи.
webapi.config.read_api_requires_server  = False
webapi.config.write_api_requires_server = False

# Интервал опроса считывателей модулем нотификации
webapi.config.notifier_poll_timeout = 0.5

# Выводить стек вызовов в числе данных о возникшей ошибке
webapi.config.error_with_traceback = True

# Максимально допустимое время для выполнения отдельной команды удаленным процессом.
# При его превышении будет сгенерирована ошибка IPCError, а не ответивший вовремя процесс
# будет принудительно остановлен (и перезапущен при подаче новой команды).
webapi.config.ipc_timeout = 5.0

# Настройки логирования
import os

app_data_folder = os.path.join(os.environ['APPDATA'],'u2')
if not os.path.exists(app_data_folder):
 os.makedirs(app_data_folder)

import logging.config
logging.config.dictConfig({
 'version': 1,    # Configuration schema in use; must be 1 for now
 'formatters': {
  'standard': {
   'format': ('%(asctime)s '
   '%(levelname)-8s %(message)s')
  }
 },
 'handlers': {
  'u2': {
   'backupCount': 10,                               # количество файлов в ротации
   'class': 'logging.handlers.RotatingFileHandler', # метод логирования
   'filename': os.path.join(app_data_folder,'u2.log'),   # имя файла
   'formatter': 'standard',
   'level': 'DEBUG',                                # уровень отладочных сообщений
   'maxBytes': 10000000                             # размер файла, после достижения которого будет выполнена ротация
  }
 },
 # Specify properties of the root logger
 'root': {
  'level': 'DEBUG',
  'handlers': ['u2'] #  используем обьявленный выше хендлер u2
 },
})

# Настройки модуля работы с бесконтактными карточками
import u2py.config

# Список системных адресов последовательных портов,
# к которым подключены считыватели БК.
# Индекс считывателей в этом списке используется в дальнейшем для
# указания считывателя для выполнения команды API
u2py.config.reader_path     = [
	#{'path': '10.0.2.195:1200', 'baud': 38400,  'impl': 'tcp'}
    #{'path': '\\\\.\\COM7', 'baud': 38400,  'impl': 'asio-mt'},
	{'path': '\\\\.\\COM3', 'baud': 38400,  'impl': 'asio-mt'},
	#{'path': '\\\\.\\COM1', 'baud': 38400,  'impl': 'blockwise'}
]

# Путь к библиотеке взаимодействия со считывателем
u2py.config.lib_filename    = 'u2.dll'

# Путь к базе данных в формате SQLite, которая хранит информацию о работе сервиса
u2py.config.db_filename     = os.path.join(app_data_folder,'db.db3')

# Идентификатор станции метрополитена, где расположен киоск
u2py.config.hall_id         = 100

# Настройки стоимости контракта на срок действия
u2py.config.term_full_cost  = 9500
u2py.config.term_half_cost  = 4800

# Стоимость 1 поездки для контракта на количество поездок
u2py.config.journey_cost    = 200

# Максимальное количество поездок, которое может содержать контракт.
# Этот параметр должен находиться в диапазоне от 0 до 2^16
u2py.config.max_journeys    = 50
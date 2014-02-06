from handlers_base import APIHandler
import config

from u2py.interface import STANDARD,ULTRALIGHT
from u2py import transport_card
from u2py import purse
from u2py import journey
from u2py import staff
from u2py import term
from u2py import ultralight

class scan(APIHandler):
 url = '/api/scan'

 need_server = config.read_api_requires_server

 def GET(self,answer={}):
  answer.update({
   'request': {
    'reader' : 'число, индекс считывателя бесконтактных карточек',
    'fast'   : 'режим выполнения команды. true - возращать только серийный номер, false - стандартный режим',
    'sn'     : 'опциональный параметр; cерийный номер требуемой бесконтактной карточки, число',
   },
   'response': {
    'error': [
        'Информация об ошибке, возникшей при выполнении вызова API.',
        'Если операция выполнилась успешно, значение этого ключа равно null',
        'Если же при выполнении вызова произошла ошибка, информация о ней имеет следующий вид:',
        {
            'type'    : 'тип возникшей ошибки',
            'message' : 'сообщение об ошибке, ключ присутствует только для системны ошибок',
            "sector"  : 'номер связанного с ошибкой сектора',
            "block"   : 'номер связанного с ошибкой блока',
            "code"    : 'код ошибки',
            "hex"     : "код ошибки в шестнадцатеричном виде",
        }
    ],
    'ultralight': 'признак карточки Mifare Ultralight',
    'time_elapsed': 'число, время затраченное на выполнение команды в секундах',
    'sn': 'Серийный номер бесконтактной карточки, число',
    'aspp': 'АСПП номер транспортной карточки, строка вида 0000000000000000',
    'end_date': 'дата завершения валидности транспортной карточки, строка в формате DD/MM/YY',
    'deposit': 'залоговая стоимость транспортной карточки, число',
    'pay_unit': 'код валюты, число',
    'resource': 'ресурс карточки, число',
    'status': 'статус контракта, число',
    'contracts': [
        'Список идентификаторов контрактов, присутствующих на транспортной карточке.',
        'В зависимости от содержимого этого списка, в ответ добавляются новые ключи с информацией о контрактах:',
        'journey - информация о контракте на количество поездок (0xD01100).',
        'staff - информация о служебном контракте (0xD010FF).',
        'personal - информация о пользователе карточки, добавляется вместе с ключом staff.'
    ],
    'purse_value': 'Сумма на транспортном кошельке, в копейках',
    'journey': {
        "status": 'статус контракта: 1 - активен, остальные значения считаются некорректными',
        "transaction": 'счетчик транзакций контракта',
#        "reserved": 'зарезервированные байты = <ef bc>',
        "journeys": 'осташееся количество поездок',
        "validated_time": 'время последней валидации контракта вида hh:mm:ss',
        "validated_date": 'дата последней валидации контракта вида DD/MM/YY',
#        "bitmap": 'версия размещения данных этого контракта на карточке = 1',
#        "version": 'версия контракта = 1',
#        "id": 'идентификатор контракта = 153'
    },
    'staff': {
        "status": 'статус контракта: 1 - активен, остальные значения считаются некорректными',
#        "double_use": {
#            "duration": 'интервал повторного прохода для контракта',
#            "unit": 'единица измерения интервала повторного прохода'
#        },
        "user_status": [
            'Статус пользователя служебной карточки, число, сумма отдельных прав пользователя',
            '1 - запрет прохода',
            '2 - статус кассира',
            '4 - статус старшего кассира',
        ],
        #"aidpix": 'идентифкатор контракта в шестнадцатеричном формате = D010FF',
        #"bitmap": 'версия размещения данных этого контракта на карточке = 0',
        #"version": 'версия контракта = 0',
        "validity_end_date": "дата окончания валидности контракта вида DD/MM/YY",
        "validity_begin_date": "дата начала валидности контракта вида DD/MM/YY",
        #"identifier": 'идентификатор контракта = 135'
    },
    'personal': {
        'fio' : 'ФИО пользователя карточки'
    },
    'term': {
        "status": 'статус контракта: 1 - активен, остальные значения считаются некорректными',
        "validity_limit_date": "дата окончания срока эксплуатации контракта вида DD/MM/YY, в данный момент не используется",
        "transaction": 'счетчик транзакций контракта',
        "validity_end_date": "дата окончания валидности контракта вида DD/MM/YY",
        "validity_begin_date": "дата начала валидности контракта вида DD/MM/YY",
        "validated_time": 'время последней валидации контракта вида hh:mm:ss',
        "validated_date": 'дата последней валидации контракта вида DD/MM/YY',
        "transport_type": 'число, соответствующее перечислению видов транспорта, доступных контракту',
    }
   }
  })

 def POST(self, reader, sn = None, answer={}, fast=False, **kw):
  card = reader.scan(sn)

  answer['sn'] = card.sn.sn7()
  answer['ultralight'] = card.type == ULTRALIGHT
  if fast: return

  if card.type == ULTRALIGHT:
   answer['term']         = ultralight.read(card)
   answer['aspp']         = str(card.aspp)
   answer['contracts']    = card.contract_list
   return

  transport_card.validate(card)
  answer['aspp']         = str(card.aspp)
  answer['end_date']     = card.end_date
  answer['deposit']      = card.deposit
  answer['pay_unit']     = card.pay_unit
  answer['resource']     = card.resource
  answer['status']       = card.status
  answer['contracts']    = card.contract_list
  answer['purse_value']  = purse.get_value(card)

  if 0xD01100 in card.contract_list:
   answer['journey'] = journey.read(card)

  if 0xD010FF in card.contract_list:
   answer['staff'] = staff.read(card)
   answer['personal'] = staff.read_personal_info(card)

  for aidpix in card.contract_list:
   if aidpix & 0xF00 == 0x300:
    answer['term'] = term.read(card)
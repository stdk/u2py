from interface import MFEx,Reader
import transport_card
import purse
import config

def api(function):
 def wrapper(kw={},**kw2):
  kw.update(kw2)
  response = {
    'function' : function.__name__,
  #  'args' : str(kw),
    'error' : 0
  }
  try:
   response['result'] = function(**kw)
  except MFEx as e:
   response['error'] = e.code
  except Exception as e:
   response['error'] = -1
   response['message'] = str(e)
  return response
 return wrapper

@api
def open_reader(path=None):
 if not path: path = config.reader_path
 return Reader(path)

@api
def scan_card(reader):
 return reader.scan()

validate_transport_card = api(transport_card.validate)
get_purse_value = api(purse.get_value)
change_purse_value = api(purse.change_value)

if __name__ == '__main__':
 reader = open_reader(path='\\\\.\\COM2')['result']
 card = scan_card(reader=reader)['result']
 print validate_transport_card(card=card)
 print change_purse_value(card=card,value=1)
 print get_purse_value(card=card)
#local development fix
if __name__ == '__main__':
 import sys
 sys.path.append('../')

import config
import os
from web import form,NotFound
from handlers_base import Handler,urls

import scan
import journey
import register
import term
import version
import card_event

class index(Handler):
 refill_journey_form = form.Form(
    form.Textbox('Amount'),
    form.Dropdown('Reader',[i for i in range(3)]),
    form.Button('Generate'),
    form.Dropdown('method', ['POST','GET']),
    form.Dropdown('URL',[url for url in urls if url.startswith('/api/')]),
    form.Textarea('Request',rows=4,cols=100),
    form.Textarea('Response',rows=20,cols=100),
    form.Button('Send')
 )

 url = '/'
 def GET(self):
  form = self.refill_journey_form()
  return self.templates.index(form)

class static(Handler):
 url = '/static/(.*)'
 def GET(self,filename):
  print 'static',filename
  try:
   path = os.path.join(config.static_folder,filename)
   return open(path, 'r').read()
  except IOError:
   raise web.NotFound()
#local development fix
if __name__ == '__main__':
 import sys
 sys.path.append('../')

import config
import os
import web
from web import form,template,NotFound
from handlers_base import Handler,urls
from pkg_resources import resource_string

import scan
import card
import journey
import register
import term
import card_event
import version
import reader
import notify

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
  return template.Template(resource_string(__name__,'templates/index.html'))(form)

class static(Handler):
 url = '/static/(.*)'

 def GET(self,filename):
  try:
   name = os.path.basename(filename)
   return resource_string(__name__,'static/' + name)
  except IOError:
   raise NotFound()

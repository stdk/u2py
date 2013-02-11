import sqlite3
import time
from u2py.db import db_connection

SERVER_TIMEOUT = 60

create_query = """
create table if not exists state (
    id INTEGER PRIMARY KEY default (null),
    activity TEXT default(0),
    stoplist INTEGER default (0)
);
replace into state(id,activity,stoplist) values(0,
 coalesce((select activity from state),0),
 coalesce((select stoplist from state),0));
"""

with db_connection as c:
 c.executescript(create_query)

class State(object):
 UPDATE_ACTIVITY_QUERY = "update state set activity = ?"
 CHECK_ACTIVITY_QUERY  = "select activity from state"

 SET_STOPLIST_QUERY = "update state set stoplist = ?"
 GET_STOPLIST_QUERY = "select stoplist from state"

 @classmethod
 def is_server_present(cls):
  with db_connection as c:
   for row in c.execute(cls.CHECK_ACTIVITY_QUERY):
    return time.time() - float(row[0]) < SERVER_TIMEOUT

 @classmethod
 def update_server_activity(cls):
  with db_connection as c:
   c.execute(cls.UPDATE_ACTIVITY_QUERY,(time.time(),))

 @classmethod
 def get_stoplist_version(cls):
  with db_connection as c:
   for row in c.execute(cls.GET_STOPLIST_QUERY):
    return int(row[0])

 @classmethod
 def set_stoplist_version(cls,version):
  with db_connection as c:
   c.execute(cls.SET_STOPLIST_QUERY,(version,))
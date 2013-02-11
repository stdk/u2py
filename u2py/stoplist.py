from db import db_connection

create_query = """
create table if not exists stoplist (
    id INTEGER PRIMARY KEY default (null),
    aspp TEXT,
    status INTEGER
);
create index if not exists aspp on stoplist(aspp);
"""

with db_connection as c:
 c.executescript(create_query)

class Stoplist(object):
 DROP_QUERY = 'drop index if exists aspp; drop table if exists stoplist;'
 SELECT_QUERY = 'select aspp,status from stoplist where aspp = ? limit 0,1'
 INSERT_QUERY = 'insert into stoplist(aspp,status) values(?,?)'

 STATUS_BLOCKED = 1

 @classmethod
 def save(cls,cards):
  with db_connection as c:
   c.executescript(cls.DROP_QUERY)
   c.executescript(create_query)
   c.executemany(cls.INSERT_QUERY,cards)

 def __contains__(self,aspp):
  with db_connection as c:
   for row in c.execute(self.SELECT_QUERY,(str(aspp),)):
    print row
    return row[1] == self.STATUS_BLOCKED

if __name__ == '__main__':
 Stoplist.save([['123',1],['234',1],['345',2]])

 print '123' in Stoplist()
 print '222' in Stoplist()
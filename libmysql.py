import MySQLdb
import MySQLdb.cursors
import string
import types
import datetime

import shapely.geometry

# obsolete, change to db.escape_string(s)
def mysql_real_escape_string(s):
    # http://id.php.net/manual/en/function.mysql-real-escape-string.php
    # mysql_real_escape_string() calls MySQL's library function mysql_real_escape_string, which prepends backslashes to the following characters: \x00, \n, \r, \, ', " and \x1a.
    s = string.replace(s,"\x00","\\x00")
    s = string.replace(s,"\n","\\n")
    s = string.replace(s,"\r","\\r")
    s = string.replace(s,"\\","\\\\")
    s = string.replace(s,"'","\\'")
    s = string.replace(s,'"','\\"')
    s = string.replace(s,"\x1a","\\x1a")
    return s

class DefaultType:
    pass

class NowType:
    pass

DEFAULT_TYPE = DefaultType()
NOW_TYPE = NowType()

class DB:
   def __init__(self, host, user, passwd, port, db):
       self.connect(host, user, passwd, port, db)

   def connect(self, host, user, passwd, port, db):
      try:
         self.db = MySQLdb.connect(host=host, user=user, passwd=passwd, port=port, db=db, cursorclass=MySQLdb.cursors.DictCursor)
         #self.db = MySQLdb.connect(host=host, user=user, passwd=passwd, port=port, db=db)

      except MySQLdb.MySQLError, e:
         print "Error(%d): %s" % (e.args[0], e.args[1])
         raise

   def query(self, sql):
      c = self.db.cursor()
      try:
         c.execute(sql)
         self.sql = sql
      except MySQLdb.MySQLError, e:
         print e, e.args
         if len(e.args) == 2:
            print "Error(%d): %s" % (e.args[0], e.args[1])
            raise
         elif len(e.args) == 1: # soft error: warning, eg. insert/update but values are truncated
            print "Error: %s" % (e.args[0])
         else:
            print "Unknown Error on query (%s)" % sql, e
            raise

      try:
         r = c.fetchall()
         d = c.description
      except:
         r = None
         d = None
      c.close()
      return ResultSet(r, d)

   def update_old(self, tn, fv, wc): # tn = table name, fv = fields values, wc = where clause
       fvs = ""
       for efv in fv: # efv each field value
           if type(fv[efv]) in [types.IntType, types.LongType, types.FloatType]:
               fvs = fvs + "%s = %s" % (efv, fv[efv])
           if type(fv[efv]) in types.StringTypes:
               fvs = fvs + "%s = '%s'" % (efv, self.db.escape_string(fv[efv]))
           if type(fv[efv]) == types.NoneType:
               fvs = fvs + "%s = NULL"
           if type(fv[efv]) in [datetime.datetime, datetime.date, datetime.time]:
               fvs = fvs + "%s = '%s'" % (efv, fv[efv].isoformat())
           if type(fv[efv]) in [shapely.geometry.Point, shapely.geometry.LineString, shapely.geometry.LinearRing, shapely.geometry.Polygon, shapely.geometry.MultiPoint, shapely.geometry.MultiLineString, shapely.geometry.MultiPolygon, shapely.geometry.GeometryCollection]:
               #fvs = fvs + "%s = GeomFromText('%s')" % (efv, fv[efv].to_wkt())
               fvs = fvs + "%s = GeomFromWKB('%s')" % (efv, self.db.escape_string(fv[efv].to_wkb()))
           if type(fv[efv]) == types.InstanceType:
               if isinstance(fv[efv], DefaultType):
                   fvs = fvs + "%s = DEFAULT" % (efv)
               elif isinstance(fv[efv], NowType):
                   fvs = fvs + "%s = NOW()" % (efv)
               else:
                   # else assign NULL 
                   fvs = fvs + "%s = NULL" % (efv)
           fvs = fvs + ", "
       fvs = fvs[:-2] # strip end comma
       self.sql = "UPDATE %s SET %s WHERE %s" % (tn, fvs, wc)
       #print self.sql
       return self.query(self.sql)

   def insert_old(self, tn, fv): # tn = table name, fv = fields values
       fvs = "("
       for efv in fv:
           fvs = fvs + efv + ", "
       fvs = fvs[:-2] # strip end comma
       fvs = fvs + ") VALUES ("

       for efv in fv:
           if type(fv[efv]) in [types.IntType, types.LongType, types.FloatType]:
               fvs = fvs + "%s" % (fv[efv])
           if type(fv[efv]) in types.StringTypes:
               fvs = fvs + "'%s'" % (self.db.escape_string(fv[efv]))
           if type(fv[efv]) == types.NoneType:
               fvs = fvs + "NULL" 
           if type(fv[efv]) in [datetime.datetime, datetime.date, datetime.time]:
               fvs = fvs + "'%s'" % (fv[efv].isoformat())
           if type(fv[efv]) in [shapely.geometry.Point, shapely.geometry.LineString, shapely.geometry.LinearRing, shapely.geometry.Polygon, shapely.geometry.MultiPoint, shapely.geometry.MultiLineString, shapely.geometry.MultiPolygon, shapely.geometry.GeometryCollection]:
               #fvs = fvs + "GeomFromText('%s')" % (fv[efv].to_wkt())
               fvs = fvs + "GeomFromWKB('%s')" % (self.db.escape_string(fv[efv].to_wkb()))
           if type(fv[efv]) == types.InstanceType:
               if isinstance(fv[efv], DefaultType):
                   fvs = fvs + "DEFAULT"
               elif isinstance(fv[efv], NowType):
                   fvs = fvs + "NOW()"
               else:
                   # else assign NULL 
                   fvs = fvs + "NULL"
           fvs = fvs + ", "
       fvs = fvs[:-2] # strip end comma
       fvs = fvs + ")"
       self.sql = "INSERT INTO %s %s" % (tn, fvs)
       #print self.sql
       return self.query(self.sql)

   def value_escaper(self, efv):
       if type(efv) in [types.IntType, types.LongType, types.FloatType]:
           r = "%s" % (efv)
       if type(efv) in types.StringTypes:
           r = "'%s'" % (self.db.escape_string(efv))
       if type(efv) == types.NoneType:
           r = "NULL" 
       if type(efv) in [datetime.datetime, datetime.date, datetime.time]:
           r = "'%s'" % (efv.isoformat())
       if type(efv) in [shapely.geometry.Point, shapely.geometry.LineString, shapely.geometry.LinearRing, shapely.geometry.Polygon, shapely.geometry.MultiPoint, shapely.geometry.MultiLineString, shapely.geometry.MultiPolygon, shapely.geometry.GeometryCollection]:
           #r = "GeomFromText('%s')" % (efv.to_wkt())
           r = "GeomFromWKB('%s')" % (self.db.escape_string(efv.to_wkb()))
       if type(efv) == types.InstanceType:
           if isinstance(efv, DefaultType):
               r = "DEFAULT"
           elif isinstance(efv, NowType):
               r = "NOW()"
           else:
               # else assign NULL 
               r = "NULL"
       #print "type(efv)", type(efv)
       return r

   def insert_sql(self, tn, fv, is_print): # tn = table name, fv = fields values
       fvs = "("
       for efv in fv:
           fvs = fvs + efv + ", "
       fvs = fvs[:-2] # strip end comma
       fvs = fvs + ") VALUES ("

       for efv in fv:
           fvs = fvs + "%s" % (self.value_escaper(fv[efv]))
           fvs = fvs + ", "
       fvs = fvs[:-2] # strip end comma
       fvs = fvs + ")"
       self.sql = "INSERT INTO %s %s" % (tn, fvs)
       if is_print:
           print self.sql

   def insert(self, tn, fv): # tn = table name, fv = fields values
       self.insert_sql(tn, fv, False)
       #print self.sql
       return self.query(self.sql)

   def update_sql(self, tn, fv, wc, is_print): # tn = table name, fv = fields values, wc = where clause
       fvs = ""
       for efv in fv: # efv each field value
           fvs = fvs + "%s = %s" % (efv, self.value_escaper(fv[efv]))
           fvs = fvs + ", "
       fvs = fvs[:-2] # strip end comma
       self.sql = "UPDATE %s SET %s WHERE %s" % (tn, fvs, wc)
       if is_print:
           print self.sql
 
   def update(self, tn, fv, wc): # tn = table name, fv = fields values, wc = where clause
       self.update_sql(tn, fv, wc, False)
       #print self.sql
       return self.query(self.sql)

   def requery(self):
      if self.sql != None:
         return self.query(self.sql)

   def begin(self):
      self.db.begin()

   def commit(self):
      self.db.commit()

   def rollback(self):
      self.db.rollback()

   def escape_string(self, s):
      return self.db.escape_string(s)

   def close(self):
      self.db.close()

class ResultSet:
   def __init__(self, r, d):
      if d == None:
         # DML, don't have description (result set)
         return
      self.rs = r
      self.FieldNames = []
      for i in range(len(d)):
         self.FieldNames.append(d[i][0])

   def __getitem__(self,i):
      return self.rs[i]

   def __str__(self):
      return str(self.rs)

   def __len__(self):
      return len(self.rs)

   def __add__(self, r):
      return self.rs + r

if __name__ == '__main__':
   db = DB("localhost","root","",3306,"mysql")
   q = db.query("SELECT * FROM user")
   q2 = db.requery()
   #q = db.query("DESCRIBE user")
   db.close()
   print q.FieldNames
   for i in range(len(q)):
      #print q[i]["User"], q[i]["Host"]
      for j in range(len(q.FieldNames)):
         print q[i][q.FieldNames[j]],
      print

   db = DB("localhost","root","",3306,"mysql")
   try:
       db.query("drop table test")
   except:
       pass
   db.query("create table test (a int default 1, b float, c datetime, d date, e time, f varchar(10), g geometry)")
   db.insert("test", {"a":DEFAULT_TYPE,"b":None, "c":datetime.datetime.now(), "d":datetime.date(2010,10,10), "e":None, "f":"a'a", g:shapely.geometry.Point(1,1)})
   print db.query("select * from test")
   db.update("test", {"a":2,"b":9.872, "c":datetime.datetime.now(), "d":datetime.date(2011,11,11), "e":datetime.time(10,10,10), "f":"a'abcd", g:shapely.geometry.Polygon([(0, 0), (1, 1), (1, 0)])}, "a = 1")
   qtest = db.query("select * from test")
   qtest + ({"a":3,"b":45.75234, "c":datetime.datetime.now(), "d":datetime.date(2012,12,12), "e":datetime.time(11,11,11), "f":"gfjgfklj'fdjle", g:shapely.geometry.Polygon([(2, 2), (3, 3), (4, 4)])}, )
   print qtest
   db.query("drop table test")
   db.rollback()
   db.close()


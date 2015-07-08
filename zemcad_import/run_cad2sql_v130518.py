#!/usr/bin/python2
# -*- coding: utf-8 -*-
from optparse import OptionParser
import sys, time, threading, getpass
import psycopg2
import cad2sql_v130519 as cad2sql

parser = OptionParser()
parser.add_option("-f", "--file", dest="filename", help="file to import")
parser.add_option("-c", "--port", type="int", dest="dbport", default=5432,
                  help="port for database connection, default 5432")
parser.add_option("-s", "--host", dest="dbhost", default="localhost", help="specify database host, default localhost")
parser.add_option("-d", "--database", dest="dbname", help="database name")
parser.add_option("-u", "--user", dest="username", help="username for database connection, default gis")
parser.add_option("-p", "--password", dest="passwd",
                  help="password for database connection, default gis, if username is specified but password is not"
                       " will prompt for it when running the program")
(options, args) = parser.parse_args()


if options.username is None and options.passwd is None:
    options.username, options.passwd = 'gis', 'gis'
elif options.username is None and options.passwd is not None:
    parser.error("can't define password without defining username")
elif options.username is not None and options.passwd is None:
    options.passwd = getpass.getpass("cad2sql - enter database password:")


#a bit complicated, checks if the file or
if options.filename is None and options.dbname is None:
    if len(args) < 2:
        parser.error("specify both file and database name")
    options.dbname = args[0]
    options.filename = args[1]
elif options.filename is None and options.dbname is not None:
    if len(args) < 1:
        parser.error("specify file")
    options.filename = args[0]
elif options.filename is not None and options.dbname is None:
    if len(args) < 1:
        parser.error("specify database name")
    options.dbname = args[0]

dbprops = "dbname=%s port=%d host=%s user=%s password=%s" % (
    options.dbname, options.dbport, options.dbhost, options.username, options.passwd)  # % cadzemdb'

print "Start"

database = None
try:
    database = psycopg2.connect(dbprops)  # ("dbname=template_postgis user=gis password=gis host='localhost' port=5432")
except Exception as e:
    print "error when connecting to database"
    print e
myCadFileName = options.filename  # 'F:\BGTopoMaps\ESRI\Todor\TMP_ALL\\04220.CAD' # ok


# myDB = psycopg2.connect("dbname=bgcad user=gis password=k2 host='localhost' port=5432")

# myCadFileName = 'F:\BGTopoMaps\ESRI\Todor\TMP_ALL\\NESLAS.CAD' # ok

# myCadFileName = "27454.CAD"

def f(fname,db):
    imp = cad2sql.czImport(fname,db)
    imp.ImportFileOrFolder(True);


threading.Thread(target=f, args=(options.filename,database)).start() #this is supposedly the preffered way to do threading in python

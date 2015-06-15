#-*- coding: utf-8 -*-

from optparse import OptionParser
import sys, os, re, string, time, threading
import psycopg2
import cad2sql_v130519 as cad2sql

parser = OptionParser()
parser.add_option("-f", "--file", dest="filename")

cadzemdb = sys.argv[1]#
czfile = sys.argv[2]


dbprops = "dbname=%s port=5432 host=localhost user=gis password=gis"  % cadzemdb # % cadzemdb'

print "Start"
MyTime = time.time()
MyTimeAll = MyTime


myDB = psycopg2.connect(dbprops)#("dbname=template_postgis user=gis password=gis host='localhost' port=5432")
myCadFileName = czfile# 'F:\BGTopoMaps\ESRI\Todor\TMP_ALL\\04220.CAD' # ok


#myDB = psycopg2.connect("dbname=bgcad user=gis password=k2 host='localhost' port=5432")

#myCadFileName = 'F:\BGTopoMaps\ESRI\Todor\TMP_ALL\\NESLAS.CAD' # ok

#myCadFileName = "27454.CAD"


class MyThread ( threading.Thread ):
    def run (self):
        myImp = cad2sql.czImport(czFileOrFolderName = myCadFileName, db = myDB)
        myImp.ImportFileOrFolder(True)
MyThread().start()



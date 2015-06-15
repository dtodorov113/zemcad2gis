# -*- coding: utf-8 -*-
#!/usr/bin/env python -
import sys, os, re, string, psycopg2, time, datetime, hashlib, logging

try:
	from osgeo import osr
	from osgeo import ogr
except ImportError:
	import osr
	import ogr


LOG_FILENAME = 'cad2sql.log'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)

magic3 = 3
magic4 = 4

fucking_magic_id = 4

class czLayer():
	def __init__ (self, name, parent):
		self.Parent = parent
		self.Name = name
		self.Texts = []
		self.Points = []
		self.Symbols = []
		self.Lines = []		
		self.Contures = []
		self.Contures_Nested = []
		self.Contures_Surround = []
		self.Dict_L = {}

	def __SQLColumns(self, _table):
		return self.Parent.GetCorrectColumns(self.Parent.IsZEM)[_table]


	def __SQLDictTexts(self, _table):
		arrKeys = self.__SQLColumns(_table)
		arrValues = []
		listTmp = []

		for item in self.Texts:
			strItem = item.strip()			
			arrValues = strItem.split(";")
			part1 = arrValues[0].strip()
			if len(arrValues)==2:
				part2 = arrValues[1].strip()

				arr1 = part1.split(" ")
				arr2 = part2.split(" ")

				arrValues = arr1
				if part2.startswith("C "):
					arrValues = arr1 + arr2
				else:
					arrValues.append(part2)
			else:	
				arr1 = part1.split(" ")
				arrValues = arr1

			razlika = (len(arrKeys) - len(arrValues)) - 3 #2 #Magic
			if razlika > 0:
				for i in range(razlika):
					#insyrtwane na tretposlednomqsto
					arrValues.insert(len(arrValues)-1,"")

			elif razlika < 0:
				for i in range(abs(razlika)):
					arrValues[len(arrValues)-2] +=" "+ arrValues[ (len(arrValues)-1) + i ]

				for i in range(abs(razlika)):
					arrValues.remove(arrValues[len(arrValues)-1])

			if len(arrValues) == len(arrKeys) - 3: #2: #Magic zaradi dwete dobaweni poleta - geom i import_id				

				x = self.Parent.RefX + float(arrValues[magic3]) #Magic!!!3
				y = self.Parent.RefY + float(arrValues[magic4]) #Magic!!!4
				arrValues.append("POINT(" + str(y) + " " + str(x) + ")")
				arrValues.insert(0, self.Parent.ImportID) #wmykwam stojnost za IMPORT_ID - w pole IMPORT_ID
				arrValues.insert(1, self.Name) #wmykwam stojnost layer_name

				dictTemp = dict( zip(arrKeys,arrValues) )
				listTmp.append(dictTemp)
			else:
				print "neeeeeeeeee Problem:\tValues: "+str(len(arrValues))+"\tKeys: "+str(len(arrKeys))
				logging.debug( "neeeeeeeeee Problem:\tValues: "+str(len(arrValues))+"\tKeys: "+str(len(arrKeys)) )
				#c = self.Parent.db.cursor()
				#c.execute("""INSERT INTO cz_error (table_name,error_record) VALUES("""+arrValues[0]+""","""+arrValues[0]+""")""")	
		return listTmp

	def __SQLDictPoints(self, _table):
		arrKeys = self.__SQLColumns(_table)
		arrValues = []
		listTmp = []		
		for item in self.Points:
			strValues = item.strip()			
			arrValues = strValues.split(" ")
			x = self.Parent.RefX + float(arrValues[magic3]) #Magic!!!3
			y = self.Parent.RefY + float(arrValues[magic4]) #Magic!!!4
			arrValues.append("POINT(" + str(y) + " " + str(x) + ")") #dobawqm stojnost za pole GEOM
			arrValues.insert(0, self.Parent.ImportID) #wmykwam stojnost za IMPORT_ID - w pole IMPORT_ID
			arrValues.insert(1, self.Name) #wmykwam stojnost layer_name

	# wariant za virtual format	
	#	nad83 = osr.SpatialReference()
	#	nad83.SetFromUserInput('NAD83')

	#	shp_driver = ogr.GetDriverByName('ESRI Shapefile')
	#	shp_driver.DeleteDataSource("c:\\aaa")

	#	shp_ds = shp_driver.CreateDataSource("c:\\aaa")
	#	shp_layer = shp_ds.CreateLayer('point_out', geom_type = ogr.wkbPolygon, srs = nad83)

	#	#src_defn = poly_layer.GetLayerDefn()
	#	#poly_field_count = src_defn.GetFieldCount()

	#	fd = ogr.FieldDefn( "Name", ogr.OFTString  )			
	#	shp_layer.CreateField( fd )

	#	g1 = ogr.CreateGeometryFromWkt( "POINT(" + str(y) + " " + str(x) + ")" )

	#	poFeature = OGRFeature( shp_layer.GetLayerDefn() )
	#	#poFeature.SetField( "Name", szName )
			for i in range(len(arrKeys) - len(arrValues)):	# dopylwam s prazni stojnosti ako kluchowete sa poweche ot stojnostite			
				arrValues.insert(len(arrValues)-1,"") #insyrtwane na predposledno mqsto
			dictTemp = dict( zip(arrKeys,arrValues) )
			listTmp.append(dictTemp)			
		return listTmp			

	def __SQLDictSymbols(self, _table):
		arrKeys = self.__SQLColumns(_table)
		arrValues = []
		listTmp = []
		for item in self.Symbols:
			strValues = item.strip()			
			arrValues = strValues.split(" ")
			x = self.Parent.RefX + float(arrValues[magic3]) #Magic!!!3
			y = self.Parent.RefY + float(arrValues[magic4]) #Magic!!!4
			arrValues.append("POINT(" + str(y) + " " + str(x) + ")") #dobawqm stojnost za pole GEOM
			arrValues.insert(0, self.Parent.ImportID) #wmykwam stojnost za IMPORT_ID - w pole IMPORT_ID
			arrValues.insert(1, self.Name) #wmykwam stojnost layer_name
			for i in range(len(arrKeys) - len(arrValues)):	# dopylwam s prazni stojnosti ako kluchowete sa poweche ot stojnostite			
				arrValues.insert(len(arrValues)-1,"") #insyrtwane na predposledno mqsto
			dictTemp = dict( zip(arrKeys,arrValues) )
			listTmp.append(dictTemp)			
		return listTmp	

	def __SQLDictLines(self, _table):
		arrKeys = self.__SQLColumns(_table)
		arrValues = []
		listTmp = []
		arr_k = []
		arr_v = []
		iLine = 0
		for item in self.Lines:
			p = re.search('[^\x20-\x7E]', item)
			if not p:
				strValues = item.replace("; ;",";").strip(";").strip()
				arrValues = strValues.split(";")	
				strValues2 = arrValues[0].strip()			
				arrValues2 = strValues2.split(" ")
				if self.Parent.IsZEM == False:
					if len(arrValues2) == 6: #magic!				
						arrValues2.append('0')
				elif len(arrValues2) == 4: #magic!				
					arrValues2.append('0')
				arrValues.remove(arrValues[0]);
				arrTmpYX = []
				ProblemInLine = False
				for el in arrValues:
					strValues3 = el.strip()
					arrValues3 = strValues3.split(" ")
					if len(arrValues3) >= 2:
						try:						    
							x = self.Parent.RefX + float(arrValues3[1])
							y = self.Parent.RefY + float(arrValues3[2])
#=========================== zapiswane na opisaniqta na linii w otdelna tablica ===========================================
							if self.Parent.FillLinePointTable == True:
								LneID = arrValues2[2] #magic!!!2
								yx = str(y) + ", " + str(x)
								c = self.Parent.db.cursor()
								##tmpSQl = """INSERT INTO cz_service_line_point ("""+"import_id, layer_name, line_id, point_xy"+""") VALUES("""+ "%s, '"%self.Parent.ImportID + self.Name + "', %s, %s" %(polyIDforServiceTable ,lineID) +""")"""
								#tmpSQl = """INSERT INTO cz_service_line_point ("""+"import_id, layer_name, line_id, point_xy"+""") VALUES("""+ "%s, '"%self.Parent.ImportID + self.Name + "', %s, '" %(LneID) + yx + """')"""
								#print tmpSQl
								#tmpSQl = """INSERT INTO cz_service_line_point ("""+"import_id, layer_name, line_id, point_xy"+""") VALUES("""+ "%s, '"%self.Parent.ImportID + self.Name + "', %s, %s" %(polyIDforServiceTable ,lineID) +""")"""
								tmpSQl = """INSERT INTO cz_service_line_point ("""+"import_id, layer_name, line_id, point_xy"+""") VALUES("""+ "%s, '"%self.Parent.ImportID + self.Name + "', %s, '" %(LneID) + yx + """')"""
								c.execute(tmpSQl)
								c.close()
								self.Parent.db.commit()
#======================================================================
							arrTmpYX.append( str(y) + " " + str(x) )
						except:
							ProblemInLine = True
							print "ERROR: " + arrValues2[2] + " / " + arrValues3[1] + " / " + arrValues3[2]
							logging.debug( "ERROR: " + arrValues3[1] + " / " + arrValues3[2] )

				if not ProblemInLine:					    
					a  = tuple(arrTmpYX)
					a1 = str(a).replace("'","")
					LneID = arrValues2[2] #magic!!!2
					arr_k.append(LneID) 
					arr_v.append(a1)
					a1 = "LINESTRING" + a1
					arrValues2.append(a1)	
					arrValues2.insert(0, self.Parent.ImportID) #wmykwam stojnost za IMPORT_ID - w pole IMPORT_ID
					arrValues2.insert(1, self.Name) #wmykwam stojnost layer_name
					dictTemp = dict( zip(arrKeys,arrValues2) )
					listTmp.append(dictTemp)
			else:
				strLog = "STRANGE SYMBOLS, SKIPED: " + item
				print strLog
				logging.debug(strLog)
		self.Dict_L =  dict( zip(arr_k, arr_v))
		return listTmp

	def __SQLDictContures(self, _table):
		arrKeys = self.__SQLColumns(_table)		
		arrValues = []
		listTmp = []
		i=0
		arrValues99 = []
		countTexts = 0
		for item in self.Contures:
			#if item.startswith("C 2 0.112 2159.43 13808.60 15.04.2003 24.02.2004;2860 8638 8852 8"):
			strValues = item.strip()
			arrValues = strValues.split(";")

			strValues2 = arrValues[0].strip()
			arrValues2 = strValues2.split(" ")
			arrValues2.insert(0, self.Parent.ImportID) #wmykwam stojnost za IMPORT_ID - w pole IMPORT_ID
			arrValues2.insert(1, self.Name) #wmykwam stojnost layer_name
			#polyIDforServiceTable = arrValues2[4] #magic!!!
			polyIDforServiceTable = arrValues2[fucking_magic_id] #magic!!!


			if len(arrKeys) == (len(arrValues2) + 1):		
				arrValues.remove(arrValues[0]);			
				arrTmpYX = []			


				strValues3  = str(tuple(arrValues))
				strValues3 = strValues3.replace("(","").replace(")","").replace("'","").replace(",","")
				p = re.compile('  +')
				strValues3 = p.sub(' ', strValues3)

				strValues3 = strValues3.strip()
				arrLinesIDs = strValues3.split(" ")

				arrPolyCoords = []
				if len(arrLinesIDs) > 0:
					brIzpusnato=0

					for lineID in arrLinesIDs:
#=========================== zapiswane na opisaniqta na konturi w otdelna tablica ===========================================
						if self.Parent.FillContureLineTable:											    
							c = self.Parent.db.cursor()					
							#tmpSQl = """INSERT INTO cz_service_conture_line ("""+"import_id, layer_name, conture_id, line_id"+""") VALUES("""+ "%s, '"%self.Parent.ImportID + self.Name + "', %s, %s" %(polyIDforServiceTable ,lineID) +""")"""						
							#tmpSQl = """INSERT INTO cz_service_conture_line ("""+"import_id, layer_name, conture_id, line_id"+""") VALUES("""+ "%s, '"%self.Parent.ImportID + self.Name + "', %s, %s" %(polyIDforServiceTable ,lineID) +""")"""      
							tmpSQl = """INSERT INTO cz_service_conture_line ("""+"import_id, layer_name, conture_id, line_id"+""") VALUES("""+ "%s, '"%self.Parent.ImportID + self.Name + "', '%s', '%s'" %(polyIDforServiceTable ,lineID) +""")"""
							c.execute(tmpSQl)
							c.close()
							self.Parent.db.commit()
#======================================================================					    

						arrLineCoords = ""
						arrLineCoords = []
						if self.Dict_L.has_key(lineID):
							strLineCoords = self.Dict_L[lineID].replace("(","").replace(")","").strip()							
							strLineCoords = strLineCoords.replace(", ", ",").strip()
							arrLineCoords = strLineCoords.split(",")
						else:
							print "k2 ERROR: Can't find LineID for CONTURE"
							logging.debug( "k2 ERROR: Can't find LineID for CONTURE" )

						#tuk trqbwa da e logikata za podrevdane na liniite w poligona
						try:
							lF = arrLineCoords[0].strip()
							lL = arrLineCoords[len(arrLineCoords)-1].strip()
						except:
							lF = ""
							lL = ""


						try:
							cF = arrPolyCoords[0].strip()
							cL = arrPolyCoords[len(arrPolyCoords)-1].strip()
						except:	
							# zadyljitelno nulirane
							cF = ""
							cL = ""


						if lL == cF:
							arrPolyCoords = arrLineCoords + arrPolyCoords
						else:
							if lL == cL:
								arrLineCoords.reverse()
								arrPolyCoords = arrPolyCoords + arrLineCoords
							else:
								if lF == cF:
									arrLineCoords.reverse()
									arrPolyCoords = arrLineCoords + arrPolyCoords
								else:
									if lF == cL:
										arrPolyCoords = arrPolyCoords + arrLineCoords
									else:
										if len(arrPolyCoords) == 0:
											if len(arrLinesIDs) == 1:
												#arrPolyCoords = arrLineCoords + arrLineCoords[0]
												arrPolyCoords = arrLineCoords
											else:							
												arrPolyCoords = arrPolyCoords + arrLineCoords						
										else:
											if cF == cL:
												arrPolyCoords = arrPolyCoords							
											else:
												brIzpusnato = brIzpusnato +1
												print "k2 ERROR: Izpusnato: " + item
												print "\nbrIzpusnato:\t"+str(brIzpusnato)
												logging.debug( "k2 ERROR: Izpusnato: " + item )
												logging.debug( "\nbrIzpusnato:\t"+str(brIzpusnato) )
												arrPolyCoords = []
												#arrPolyCoords = arrPolyCoords + arrLineCoords


												c = self.Parent.db.cursor()												
												tmpSQl = """INSERT INTO cz_error (layer_name, object_type, objet_id, note) VALUES('"""+self.Name+"""', '"""+"""conture"""+"""', '"""+str(polyIDforServiceTable)+"""', '"""+"""skipped conture"""+"""')"""
												#print tmpSQl
												c.execute(tmpSQl)												

												c.close()
												self.Parent.db.commit()



						#dotuk trqbwa da e logikata za podrevdane na liniite w poligona


					if len(arrPolyCoords) > 0:
						if arrPolyCoords[0] != arrPolyCoords[len(arrPolyCoords)-1]:
							i = i+1
							print "k2 ERROR: unclosed conture, count: "+ str(i)
							logging.debug( "k2 ERROR: unclosed conture, count: "+ str(i) )
						else:
							strPolyCoords = str( tuple(arrPolyCoords) )
							strPolyCoords = strPolyCoords.replace("'","")
							strPolyCoords = "POLYGON(" +strPolyCoords +")"

							#tuk trqbwa da e logikata za ostrowi
							#polyID = arrValues2[2] #magic
							#polyID = arrValues2[4] #magic
							polyID = arrValues2[fucking_magic_id] #magic

							#cc = self.ControlLayers_Surround["CONTROL_CADASTER"]
							ll_s = self.Parent.ControlLayers_Surround[self.Name.replace("layer","control")]
							ll_n = self.Parent.ControlLayers_Nested[self.Name.replace("layer","control")]
							#ako polygona go ima kato WYTRESHEN
							daliDaApendwam = True
							for e1 in ll_s:
								str1 = e1.split(" ")
								if polyID == str1[0]:									
									myC = czContur(Id = polyID)
									myC.Coordinates.append(strPolyCoords)
									#_lyr.Contures_Surround.append(myC)
									self.Contures_Surround.append(myC)
									#daliDaApendwam = False


							#ako polygona go ima kato WYNSHEN							
							for e2 in ll_n:
								str2 = e2.split(" ")
								if polyID == str2[0]:
									myC = czContur(Id = polyID)
									myC.Coordinates.append(strPolyCoords)
									#_lyr.Contures_Nested.append(myC)
									self.Contures_Nested.append(myC)

									daliDaApendwam = False
									arrValues99.append(arrValues2)

							if daliDaApendwam == True:
								arrValues2.append(strPolyCoords)
								dictTemp = dict( zip(arrKeys,arrValues2) )
								listTmp.append(dictTemp)

	#		else:				
	#			#print str(countTexts) + " / " + str(len( _lyr.Texts))
	#			#print _lyr.Texts[countTexts] + " / " + strValues2 
	#			_lyr.Texts[countTexts] += " " + strValues2
	#			countTexts += 1
	#			if len(arrValues2) > 5:
	#				print strValues2
	#			
	#							
	#	for el in _lyr.Texts:
	#		print str(len( el.split(" ") )) + "==" + el



		#tuk trqbwa da dobawq poligonite s ostrowi
		ll_nn = self.Parent.ControlLayers_Nested[self.Name.replace("layer","control")]

		for elSur in ll_nn:
			arrSur = elSur.split(" ")
			idOut = arrSur[0]
			arrSur.remove(arrSur[0]);
			strCoordsOut = ""
			#for elNes in arrSur:				
			for b1 in self.Contures_Nested:
				if b1.Id == idOut:
					coordsOut = b1.Coordinates
					strCoordsOut = str(tuple(coordsOut))
					strCoordsOut = strCoordsOut.replace(")',)","))")

					strCoordsOut = strCoordsOut.replace("('POLY", "POLY")
					strCoordsOut = strCoordsOut.replace(")))", "))")

					tstBr=0
					for elNes in arrSur:
						#for b0 in _lyr.Contures_Surround:
						for b0 in self.Contures_Surround:
							if b0.Id == elNes:
								tstBr = tstBr + 1
								coordsIn = b0.Coordinates
								strCoordsIn = str(tuple(coordsIn))
								strCoordsIn = strCoordsIn.replace("('POLYGON(","")
								strCoordsIn = strCoordsIn.replace(")',)","")
								strCoordsOut = strCoordsOut.replace("))", "),"+strCoordsIn+")")


			for aa in arrValues99:
				#TODO MAGIC
				if aa[fucking_magic_id]==idOut:
					aa.append(strCoordsOut)		

		dictTemp1 = {}
		#listTmp = [] #za test ostwqm samo poligonite s dupki
		for i in arrValues99:
			dictTemp1 = dict( zip(arrKeys,i) )
			listTmp.append(dictTemp1)

		#dotuk trqbwa da dobawq poligonite s ostrowi

		return listTmp











	def __SQLDictConturesInnerPoints(self, _table):
		arrKeys = self.__SQLColumns(_table)		
		listTmp = []

		arrValues99 = []
		countTexts = 0
		for item in self.Contures:
			strValues = item.strip()
			arrValues = strValues.split(";")

			strValues2 = arrValues[0].strip()
			arrValues2 = strValues2.split(" ")


			isCoordsOK = True
			try:
				x = self.Parent.RefX + float(arrValues2[magic3]) #Magic!!!3
				y = self.Parent.RefY + float(arrValues2[magic4]) #Magic!!!4
			except:
				isCoordsOK = False


			if isCoordsOK:
				arrValues2.append("POINT(" + str(y) + " " + str(x) + ")") #dobawqm stojnost za pole GEOM
				arrValues2.insert(0, self.Parent.ImportID) #wmykwam stojnost za IMPORT_ID - w pole IMPORT_ID
				arrValues2.insert(1, self.Name) #wmykwam stojnost layer_name

				for i in range(len(arrKeys) - len(arrValues2)):	# dopylwam s prazni stojnosti ako kluchowete sa poweche ot stojnostite			
					arrValues2.insert(len(arrValues2)-1,"") #insyrtwane na predposledno mqsto

				dictTemp = dict( zip(arrKeys,arrValues2) )
				listTmp.append(dictTemp)

		return listTmp			





	def __ListToDict(self, _table):
		dictTmp	= {}
		if _table == "_p":		
			dictTmp = self.__SQLDictPoints(_table)
		elif _table == "_s":
			dictTmp = self.__SQLDictSymbols(_table)
		elif _table == "_t":
			dictTmp = self.__SQLDictTexts(_table)
		elif _table == "_l":
			dictTmp = self.__SQLDictLines(_table)
		elif _table == "_c":
			dictTmp = self.__SQLDictContures(_table)
		elif _table == "_i":
			dictTmp = self.__SQLDictConturesInnerPoints(_table)


		return dictTmp	






	def ImportFeaturesToBD(self, _table):
		try:

			#tableName = self.Name + _table
			#tableName = self.Name +"_"+str(self.Parent.ImportID)+_table
			#tableName = "id_" + str(self.Parent.ImportID) + "_" + self.Name + _table
			tableName = "id_" + str(self.Parent.ImportID) + "_" + self.Name + _table + "_id"

			columns = self.Parent.GetCorrectColumns(self.Parent.IsZEM)[_table]		
			dictForSQL = self.__ListToDict(_table)

			if len(dictForSQL) > 0:			
				strKeysForTable = " varchar(250), ".join([col for col in columns])

				strKeys = ",".join([col for col in columns])
				strValues = ")s,%(".join([col for col in columns])
				strValues = "%(" + strValues + ")s"		

				c = self.Parent.db.cursor()
				c.execute("SELECT * FROM pg_class WHERE relname = '" + tableName.lower() + "'")
				if len(c.fetchall()) == 0:
					c.execute("CREATE TABLE "+tableName+"( id serial NOT NULL, "+strKeysForTable+" geometry)")				
				c.execute("set client_encoding to 'WIN'")
				c.executemany("""INSERT INTO """+tableName+"""("""+strKeys+""") VALUES("""+strValues+""")""", dictForSQL)		

				c.close()
				self.Parent.db.commit()
				strLog = "Imported " + str(len(dictForSQL))+ "["+_table+"] in Layer:" + self.Name
				print strLog
				logging.debug(strLog)
			else:
				strLog = "Empty ["+_table+"] Array in Layer:" + self.Name
				print strLog
				logging.debug(strLog)

		#except Exception as inst:
		except :
			#c.close()
			self.Parent.db.commit()
			print "ERROR: ImportFeaturesToBD:" + self.Name + _table
			logging.debug( "ERROR: ImportFeaturesToBD:"+ self.Name+ _table )
			#print type(inst)     # the exception instance
			#print inst.args      # arguments stored in .args






	def FeaturesToOGR(self, _table):
		print "a"
		dictForSQL = self.__ListToDict(_table)
		if len(dictForSQL) > 0:
			for el in dictForSQL:
				print el
				ogrPoint = ogr.Feature(ogr.FeatureDefn())

				#ppp =  osgeo.ogr.Feature.p RPoint ()
				#feat = osgeo.ogr.CreateGeometryFromWkt ogr.Feature()# (feature_def=shp_layer.GetLayerDefn())
				#osgeo.osr


class czContur():
	def __init__ (self, Id):
		self.Id = Id
		self.Coordinates = []


class czFileHandler():
	arr1970 = [
	        {'zone':'k3', 'proj4':'+proj=lcc +lat_1=43.45678000 +lat_2=43.45680000 +lat_0=3.86550343 +lon_0=23.19729755 +x_0=8496745.16350000 +y_0=0.0 +ellps=krass +towgs84=24,-123,-94,0.02,-0.25,-0.13,1.1 +units=m +no_defs'},
	        {'zone':'k5', 'proj4':'+proj=lcc +lat_1=42.47925500 +lat_2=42.47927500 +lat_0=3.51876580 +lon_0=26.38994424 +x_0=9497002.61430000 +y_0=0.0 +ellps=krass +towgs84=24,-123,-94,0.02,-0.25,-0.13,1.1 +units=m +no_defs'},
	        {'zone':'k7', 'proj4':'+proj=lcc +lat_1=43.56352000 +lat_2=43.56354000 +lat_0=3.97536005 +lon_0=26.23175436 +x_0=9503619.34450000 +y_0=0.0 +ellps=krass +towgs84=24,-123,-94,0.02,-0.25,-0.13,1.1 +units=m +no_defs'},
	        {'zone':'k9', 'proj4':'+proj=lcc +lat_1=42.29330889 +lat_2=42.29332889 +lat_0=3.92530164 +lon_0=23.41990955 +x_0=8506383.44450000 +y_0=0.0 +ellps=krass +towgs84=24,-123,-94,0.02,-0.25,-0.13,1.1 +units=m +no_defs'},
	]
	tableColumnsService = {		
	        #"cz_import"   : ("source", "checksum", "import_time", "ekt"),
	        "cz_import"   : ("cz_source", "cz_checksum", "cz_import_time", "cz_format", "cz_prefix", "cz_COMMENT", "cz_CONTENTS", "cz_COORDTYPE", "cz_DATE", "cz_FIRM", "cz_NAME", "cz_PLANDATA", "cz_PLANNOMER", "cz_PLANSIGN", "cz_PROGRAM", "cz_REFERENCE", "cz_SCALE", "cz_VERSION", "cz_WINDOW", "cz_EKATTE", "cz_EKNM", "cz_PLANNUMBER"),
	        "cz_error"   : ("layer_name", "object_type", "objet_id", "note"),
	        "cz_service_conture_line"   : ("import_id", "layer_name", "conture_id", "line_id"),
	        "cz_service_line_point"   : ("import_id", "layer_name", "line_id", "point_xy",),
	        };	
	tableColumnsCAD = {

	        "_p"   : ("import_id", "layer_name", "pstlc", "t", "n", "x", "y", "h", "k", "mx", "my", "kh", "mh", "mst", "msg", "sgn", "cen", "ono", "b", "d", "geom"),
	        "_s"   : ("import_id", "layer_name", "pstlc", "t", "n", "x", "y", "a", "m", "b", "d", "geom"),
	        "_t"   : ("import_id", "layer_name", "pstlc", "t", "n", "x", "y", "h", "b", "d", "r", "j", "ps", "tnp", "ss", "geom"),
	        "_c"   : ("import_id", "layer_name", "pstlc", "t", "n", "x", "y", "b", "d", "geom"),
	        "_l"   : ("import_id", "layer_name", "pstlc", "t", "n", "k", "b", "d", "h", "geom"),
	        "_i"  : ("import_id", "layer_name", "pstlc", "t", "n", "x", "y", "b", "d", "geom"),		

	        };
	tableColumnsZEM = {
	        "_p"   : ("import_id", "layer_name", "pstlc", "t", "n", "x", "y", "h", "k", "mx", "geom"),
	        "_s"   : ("import_id", "layer_name", "pstlc", "t", "n", "x", "y", "a", "m",  "geom"),
	        "_t"   : ("import_id", "layer_name", "pstlc", "t", "n", "x", "y", "h", "b", "d", "r", "j", "ps", "tnp", "ss", "geom"),		
	        "_c"   : ("import_id", "layer_name", "pstlc", "t", "n", "x", "y", "geom"),
	        "_l"   : ("import_id", "layer_name", "pstlc", "t", "n", "k", "h", "geom"),
	        "_i"  : ("import_id", "layer_name", "pstlc", "t", "n", "x", "y", "geom"),		

	        };	


	def __init__ (self, czFullFileName, db):
		self.newLayers = []
		self.Area = []
		self.ControlLayers_Nested = {}
		self.ControlLayers_Surround = {}
		self.Tables = {}
		self.TablesColumns = {}
		self.Header = {}		

		self.PreparedLines = []


		self.current = None
		self.db = db
		self.czFullFileName = czFullFileName

		(dirName, self.czFileName) = os.path.split(czFullFileName)
		(fileBaseName, fileExtension)=os.path.splitext(self.czFileName)

		#self.preparedFileName = czFullFileName + "_prepared"
		(root, onlyDirName) = os.path.split(dirName)
		newRoot = os.path.join(root, onlyDirName + "_prepared") 
		self.preparedFileName = os.path.join(newRoot, self.czFileName + "_prepared")
		try:
			os.mkdir(newRoot)
		except:
			print "dir exist"


		self.ImportTime = time.strftime("%Y-%m-%d %H:%M:%S")


		self.Version = ""
		self.EKATTE = ""		
		self.Scale = ""
		self.RefX = 0
		self.RefY = 0
		self.Zone1970 = ""
		self.SRID = ""
		self.Proj4 = ""
		self.WKT = ""
		self.Contents = ""
		self.Comment = ""
		self.MD5 = ""
		self.ImportID = -1


		self.IsZEM = True
		self.FileFormat = "ZEM"		
		self.FormatPrefix = "z_"

		self.FillContureLineTable = False
		self.FillLinePointTable = False




		#for t in self.tableColumnsCAD.items():
		#	self.CreateTable(t)


	#def CreateTable (self,_table):
	#	print _table


# PRIVATE MEHODS
	def __CreateServiceTables(self):
		#cikyl kojto syzdawa slujebnite tablici	
		c = self.db.cursor()		
		c.execute("set client_encoding to 'WIN'")			
		for table, columns in self.tableColumnsService.items():
			strKeysForTable = " varchar(256), ".join([col for col in columns])

			c.execute("SELECT * FROM pg_class WHERE relname = '" + table.lower() + "'")
			if len(c.fetchall()) == 0:			
				c.execute("CREATE TABLE "+table+"( id serial NOT NULL, "+strKeysForTable+"  varchar(256))")				

		self.db.commit()			
		self.__AddToImportTable()
		self.ImportID = self.__GetIdByCheckSum()
		print self.ImportID
		logging.debug( self.ImportID )


	def __AddToImportTable(self):
		c = self.db.cursor()
		dictTmp = self.Header
		dictTmp["SOURCE"] = self.czFileName
		dictTmp["CHECKSUM"] = self.MD5
		dictTmp["IMPORT_TIME"] = self.ImportTime
		dictTmp["FORMAT"] = self.FileFormat
		dictTmp["PREFIX"] = self.FormatPrefix

		strKeysService = ",".join(["cz_"+key.lower() for key in dictTmp.keys()])
		strValuesService = "','".join([val for val in dictTmp.values()])

		strKeysService = strKeysService
		strValuesService = "'" + strValuesService + "'"

		c.execute("""INSERT INTO cz_import ("""+strKeysService+""") VALUES("""+strValuesService+""")""")
		c.close()
		self.db.commit()				


	def __GetIdByCheckSum(self):
		c = self.db.cursor()
		c.execute("""SELECT id FROM cz_import WHERE cz_checksum = '"""+self.MD5+"""' ORDER BY id DESC LIMIT 1""")		
		try:
			result = c.fetchall()[0][0]
		except:
			result = -1
		c.close()		
		return result


	def __DetermineFormatPrefixByLineAttributeCount(self, _fileAsString):
		p = re.search('L (.*);', _fileAsString)
		if p:			
			s = p.group().strip()		
			c = (s[0:s.find(";")]).count(" ") + 1

		if c == 4: #magic!!!
			return "z_"	
		elif c == 6: #magic!!!
			return "c_"
		elif c == 7: #magic!!!
			return "c_"		
		else:
			return "unk_"


	def GetCorrectColumns	(self, _isZEM):
		tmpColumns = {}
		if _isZEM:
			tmpColumns = self.tableColumnsZEM
		else:
			tmpColumns = self.tableColumnsCAD

		return tmpColumns	








# END PRIVATE METHODS

	def Sumarize(self, _resultTable, _sourceTables):
		GeomType = ""
		if _sourceTables.endswith("_p_id"):
			GeomType = "POINT"
		elif _sourceTables.endswith("_s_id"):
			GeomType = "POINT"	
		elif _sourceTables.endswith("_t_id"):
			GeomType = "POINT"				
		elif _sourceTables.endswith("_c_id"):
			GeomType = "POLYGON"				
		elif _sourceTables.endswith("_l_id"):
			GeomType = "LINESTRING"				
		elif _sourceTables.endswith("_i_id"):
			GeomType = "POINT"				




		plpy = self.db.cursor()
		plpy.execute("SELECT relname FROM pg_class WHERE relname LIKE '" + _sourceTables + "'");
		arrTables = plpy.fetchall()


		if len(arrTables) > 0:
			arrColumns = []
			for t in arrTables:
				plpy.execute( "SELECT a.attname FROM pg_catalog.pg_attribute a WHERE a.attnum > 0 AND NOT a.attisdropped AND a.attrelid = (SELECT c.oid FROM pg_catalog.pg_class c LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace WHERE c.relname ~ '^(" + t[0] + ")$' AND pg_catalog.pg_table_is_visible(c.oid))" );
				tmpColumns = plpy.fetchall()
				for c in tmpColumns:
					arrColumns.append(c[0])      

			arrColumns = reduce(lambda l, x: x not in l and l.append(x) or l, arrColumns, [])

			#truq poleta: id i geom
			arrColumns.remove("id");
			if not _sourceTables.endswith("_tbl"):
				arrColumns.remove("geom")				

			strKeysNew = " varchar(256), ".join([col for col in arrColumns])  
			strKeysNew += "  varchar(256)"

			strKeysNew = "gid serial NOT NULL, id serial NOT NULL, " + strKeysNew
			if not _sourceTables.endswith("_tbl"):
				strKeysNew += ", geom geometry" 

			plpy.execute("SELECT * FROM pg_class WHERE relname = '" + _resultTable + "'")
			if len(plpy.fetchall()) == 0:
				if not _sourceTables.endswith("_tbl"):



					plpy.execute("CREATE TABLE " + _resultTable + "( " + strKeysNew + 
					             ", CONSTRAINT " + _resultTable + "_pkey PRIMARY KEY (gid) " +
					             ", CONSTRAINT enforce_dims_geom CHECK (st_ndims(geom) = 2) " +
					             #", CONSTRAINT enforce_geotype_geom CHECK (st_geometrytype(geom) = '" + GeomType + "'::text OR geom IS NULL)" +
					             # Wariant na Todor za postgi 2
					             ", CONSTRAINT enforce_srid_geom CHECK (st_srid(geom) = (0))" + 					             
					             #", CONSTRAINT enforce_srid_geom CHECK (st_srid(geom) = (-1))" + 
					             ")")



					plpy.execute("CREATE INDEX " + _resultTable + "_geom_gist ON " + _resultTable + " USING gist (geom)")
				else:
					plpy.execute("CREATE TABLE " + _resultTable + "( " + strKeysNew + 
					             ", CONSTRAINT " + _resultTable + "_pkey PRIMARY KEY (gid) " +
					             ")")


			else:
				plpy.execute( "SELECT a.attname FROM pg_catalog.pg_attribute a WHERE a.attnum > 0 AND NOT a.attisdropped AND a.attrelid = (SELECT c.oid FROM pg_catalog.pg_class c LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace WHERE c.relname ~ '^(" + _resultTable + ")$' AND pg_catalog.pg_table_is_visible(c.oid))" );
				tmpColumnsOld = plpy.fetchall()
				arrColumnsOld = []
				for c in tmpColumnsOld:
					arrColumnsOld.append(c[0]) 


				arrDiff1 = [item for item in arrColumns if not item in arrColumnsOld]			
				arrDiff  = arrDiff1
				arrDiff = reduce(lambda l, x: x not in l and l.append(x) or l, arrDiff, [])			

				if len (arrDiff) > 0:
					for c in arrDiff:
						plpy.execute( "ALTER TABLE " + _resultTable + " ADD COLUMN " + c + " varchar(256)" );	


			for t in arrTables:
				plpy.execute( "SELECT a.attname FROM pg_catalog.pg_attribute a WHERE a.attnum > 0 AND NOT a.attisdropped AND a.attrelid = (SELECT c.oid FROM pg_catalog.pg_class c LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace WHERE c.relname ~ '^(" + t[0] + ")$' AND pg_catalog.pg_table_is_visible(c.oid))" );
				tmpColumns = plpy.fetchall()
				arrTmp = []
				for c in tmpColumns:      
					arrTmp.append(c[0])      

				strKeys = ", ".join([col for col in arrTmp])    

				plpy.execute( "INSERT INTO " + _resultTable + " (" + strKeys + ") SELECT * FROM " + t[0] );	
				plpy.execute( "DROP TABLE " + t[0] );	


			if not _sourceTables.endswith("_tbl"):	
				plpy.execute( "select * from geometry_columns where f_table_name = '" + _resultTable + "'")
				if len( plpy.fetchall() ) == 0:
					plpy.execute( "INSERT INTO geometry_columns (f_table_catalog, f_table_schema, f_table_name, f_geometry_column, coord_dimension, srid, type) "+
					              "VALUES('','public','" + _resultTable + "','geom',2,-1,'" + GeomType + "')" )

				#zakomentareno wpiswane w tablica "spatial_ref_sys"
				#plpy.execute( "select * from spatial_ref_sys where srid = '" + self.SRID + "'")	
				#if len( plpy.fetchall() ) == 0:
				#	plpy.execute( "INSERT INTO spatial_ref_sys (srid, auth_name, auth_srid, srtext, proj4text) " +
				#		      "VALUES (" + self.SRID + ", 'EPSG', " + self.SRID + ", '', '" + self.Proj4 + "')")





			plpy.close()
			self.db.commit()






	def PrepareFileNew(self):
		fi = open(self.czFullFileName, 'r')
		fo = open(self.preparedFileName, 'w')

		strTmp = fi.read()

		p = re.compile('  +')
		strTmp = p.sub(' ', strTmp)
		p = re.compile('\n')
		strTmp = p.sub('::', strTmp)

		p = re.compile('::LAYER')
		strTmp = p.sub('\nLAYER', strTmp)
		p = re.compile('::TABLE')
		strTmp = p.sub('\nTABLE', strTmp)
		p = re.compile('::CONTROL')
		strTmp = p.sub('\nCONTROL', strTmp)






		#p = re.compile('\n\s')
		#strTmp = p.sub(';', strTmp)
		#p = re.compile('\n\s')
		#strTmp = p.sub('\n', strTmp)



		#p = re.compile('\nT ')
		#strTmp = p.sub('***T ', strTmp)

	#	p = re.search('T (.*)\nC ', strTmp)
	#	if p:
	#		s_old = p.group().strip()
	#		s_new = s_old.replace("\n", "***")
	#		p = re.compile(s_old)
	#		strTmp = p.sub(s_new, strTmp)






#		p = re.compile('"')
#		strTmp = p.sub('', strTmp)

		fo.write(strTmp)

		fi.close()
		fo.close()


		#[[x for x in line.split()] for line in open(self.preparedFileName)]
		#[self.PreparedLines.append(line) for line in open(self.preparedFileName)]
		self.KoiToWin()

		arr1=[]
		for line in open(self.preparedFileName):
			arr1.append(line)
		print len(arr1)
		logging.debug( arr1 )






	def PrepareFile(self):
		fi = open(self.czFullFileName, 'r')
		fo = open(self.preparedFileName, 'w')

		strTmp = fi.read()

		p = re.compile('  +')
		strTmp = p.sub(' ', strTmp)

		p = re.compile('\r') # za npwite redowe pod linux
		strTmp = p.sub('', strTmp)

		#p = re.compile('\n\s')
		#strTmp = p.sub(';', strTmp)
		p = re.compile('\n\s')
		strTmp = p.sub('\n', strTmp)

		p = re.compile('\n0')
		strTmp = p.sub(';0', strTmp)
		p = re.compile('\n1')
		strTmp = p.sub(';1', strTmp)
		p = re.compile('\n2')
		strTmp = p.sub(';2', strTmp)
		p = re.compile('\n3')
		strTmp = p.sub(';3', strTmp)
		p = re.compile('\n4')
		strTmp = p.sub(';4', strTmp)
		p = re.compile('\n5')
		strTmp = p.sub(';5', strTmp)
		p = re.compile('\n6')
		strTmp = p.sub(';6', strTmp)
		p = re.compile('\n7')
		strTmp = p.sub(';7', strTmp)
		p = re.compile('\n8')
		strTmp = p.sub(';8', strTmp)
		p = re.compile('\n9')
		strTmp = p.sub(';9', strTmp)

		p = re.compile('\n\"')
		strTmp = p.sub(';\"', strTmp)

		p = re.compile(';LAYER ')
		strTmp = p.sub('\nLAYER ', strTmp)
		p = re.compile(';CONTROL ')
		strTmp = p.sub('\nCONTROL ', strTmp)
		p = re.compile(';ET ')
		strTmp = p.sub('\nET ', strTmp)
		p = re.compile('END_LAYER;')
		strTmp = p.sub('END_LAYER\n;', strTmp)

		p = re.compile(';TABLE ')
		strTmp = p.sub('\nTABLE ', strTmp)

		#p = re.compile('\nT ')
		#strTmp = p.sub('***T ', strTmp)

	#	p = re.search('T (.*)\nC ', strTmp)
	#	if p:			
	#		s_old = p.group().strip()
	#		s_new = s_old.replace("\n", "***")
	#		p = re.compile(s_old)
	#		strTmp = p.sub(s_new, strTmp)






		p = re.compile('"')
		strTmp = p.sub('', strTmp)	
		p = re.compile('  +')
		strTmp = p.sub(' ', strTmp)



		#opredelqne na formata po broj atributi na liniq
		self.FormatPrefix = self.__DetermineFormatPrefixByLineAttributeCount(strTmp)
		if self.FormatPrefix == "c_":
			self.IsZEM = False






		fo.write(strTmp)

		fi.close()
		fo.close()


		#[[x for x in line.split()] for line in open(self.preparedFileName)]
		#[self.PreparedLines.append(line) for line in open(self.preparedFileName)]
		self.KoiToWin()

	def KoiToWin(self):
		dstsrch = [chr(191),chr(192),chr(193),chr(194),chr(195),chr(196),chr(197),chr(198),chr(199),chr(200),chr(201),chr(202),chr(203),chr(204),chr(205),chr(206),chr(207),chr(208),chr(209),chr(210),chr(211),chr(212),chr(213),chr(214),chr(215),chr(216),chr(217),chr(218),chr(219),chr(220),chr(221),chr(222),chr(223),chr(224),chr(225),chr(226),chr(227),chr(228),chr(229),chr(230),chr(231),chr(232),chr(233),chr(234),chr(235),chr(236),chr(237),chr(238),chr(239),chr(240),chr(241),chr(242),chr(243),chr(244),chr(245),chr(246),chr(247),chr(248),chr(249),chr(250),chr(251),chr(252),chr(253),chr(254),chr(255)]
		srcsrch = [chr(127),chr(128),chr(129),chr(130),chr(131),chr(132),chr(133),chr(134),chr(135),chr(136),chr(137),chr(138),chr(139),chr(140),chr(141),chr(142),chr(143),chr(144),chr(145),chr(146),chr(147),chr(148),chr(149),chr(150),chr(151),chr(152),chr(153),chr(154),chr(155),chr(156),chr(157),chr(158),chr(159),chr(160),chr(161),chr(162),chr(163),chr(164),chr(165),chr(166),chr(167),chr(168),chr(169),chr(170),chr(171),chr(172),chr(173),chr(174),chr(175),chr(176),chr(177),chr(178),chr(179),chr(180),chr(181),chr(182),chr(183),chr(184),chr(185),chr(186),chr(187),chr(188),chr(189),chr(190),chr(191)]

		fi = open(self.preparedFileName)
		strTmp = fi.read()

		self.MD5 = hashlib.md5(strTmp).hexdigest()

		for a, b in zip(srcsrch, dstsrch):
			strTmp = strTmp.replace(a, b)
		fi.close
		fo = open(self.preparedFileName, 'w')
		fo.write(strTmp)
		fo.close

		PreparedLines = []
		[self.PreparedLines.append(line) for line in open(self.preparedFileName)]




	def FillLayersAndTablesFromPreparedFile(self):
		# for tables
		strTableDictName = ""
		arrTableRecords = []
		arrTableColumns = []
		arrTableDictKey = []
		arrTableDictValueColumns = []
		arrTableDictValueRecords = []

		# for control layers
		strControlLayerDictName = ""
		arrControlLayerRecords_Nested = []
		arrControlLayerDictValue_Nested = []
		arrControlLayerDictKey_Nested = []

		arrArea = []

		arrControlLayerRecords_Surround = []
		arrControlLayerDictValue_Surround = []
		arrControlLayerDictKey_Surround = []

		tmpIsHeaderLine = False
		countL = 0
		countAttributesInL = 0		
		for line in open(self.preparedFileName):
		#for line in self.PreparedLines:
			if line.startswith("HEADER"):
				tmpIsHeaderLine = True
			if tmpIsHeaderLine == True:
				if not line.startswith("HEADER") and not line.startswith("END_HEADER"):
					HeaderValue = line[0:line.find(" ")]
					self.Header[HeaderValue] = line.replace(HeaderValue,"").strip()						
			if line.startswith("END_HEADER"):
				tmpIsHeaderLine = False

				if self.Header.has_key("REFERENCE"): 
					arrTmp = self.Header["REFERENCE"].split(" ")
					if len(arrTmp) == 2:
						self.RefX = float(arrTmp[0])
						self.RefY = float(arrTmp[1])
						if arrTmp[1][0] == "0": #k3,k9
							if self.RefX > 9670000:
								self.Zone1970 = "k3"
							else:
								self.Zone1970 = "k9"
						if arrTmp[1][0] == "0": #k5,k7
							if self.RefX > 9790000:
								self.Zone1970 = "k5"
							else:
								self.Zone1970 = "k7"


				if self.Header.has_key("VERSION"): self.Version = self.Header["VERSION"]						
				if self.Header.has_key("EKATTE"): self.EKATTE = self.Header["EKATTE"]					
				if self.Header.has_key("SCALE"): self.Scale = self.Header["SCALE"]
				if self.Header.has_key("CONTENTS"): self.Contents = self.Header["CONTENTS"]
				if self.Header.has_key("COMMENT"): self.Comment = self.Header["COMMENT"]

				if self.Header.has_key("COORDTYPE"):					
					arrTmp = self.Header["COORDTYPE"].replace(" ", "").split(",")
					#if len(arrTmp) == 3:                    #Tova dava problemi za SHumenskite fajlove
					#	self.Zone1970 = "k"+arrTmp[2][1]
					if len(arrTmp) == 3:
						if len(arrTmp[2]) > 0:
							self.Zone1970 = "k"+arrTmp[2][1]

				try:
					self.SRID = "1970" + self.Zone1970[1]
				except:
					self.SRID = "1970 unkn"
				for el in self.arr1970:
					if el["zone"] == self.Zone1970:
						self.Proj4 = el["proj4"]
						#self.WKT # da se dobawi kogato imam raborshta gdal biblioteka za python 2.6

				#setwane na imena ot headera		

				#opredelqne na formata po dokimetirano opisanie
				if self.Version.startswith("4"):
					self.FileFormat = "CAD" 
				elif self.Version.startswith("3") and self.Scale == "":
					self.FileFormat = "CAD" 
				elif self.Version.startswith("2") and self.Scale == "":
					self.FileFormat = "CAD" 
				elif self.Version.startswith("1") and self.Scale == "":
					self.FileFormat = "CAD" 

				if self.FileFormat == "CAD" and self.FormatPrefix == "z_":
					self.FormatPrefix =  "c" + self.FormatPrefix + self.Version.replace(".","_") + "_"
				else:
					self.FormatPrefix += self.Version.replace(".","_") + "_"

				for col in self.tableColumnsService["cz_import"]:
					if not self.Header.has_key(col.replace("cz_", "")):
						if(col!="cz_source" and col!="cz_checksum" and col!="cz_import_time" and col!="cz_format" and col!="cz_prefix"):
							self.Header[col.replace("cz_", "")] = ""									






			#nachalo na layer
			elif line.startswith("LAYER "):				
				lyr = czLayer(name = self.FormatPrefix + (line.replace(" ","_").strip().lower()), parent = self )
			#obrabotwam red za layer
			elif line.startswith("T "):			
				lyr.Texts.append(line.strip())		
			elif line.startswith("P "):			
				lyr.Points.append(line.strip())
			elif line.startswith("S "):			
				lyr.Symbols.append(line.strip())
			elif line.startswith("L "):	
				#if countL < 10:
				#	countL += 1
				#	countAttributesInL += (line[0:line.find(";")]).count(" ") + 1				
				lyr.Lines.append(line.strip())
			elif line.startswith("C "):
				ItemsCount = len(line.strip().split(" "))
				if ItemsCount <= 4: #Magic!!! dyljina na opicanie na teksta T(sledwa red T )
					lyr.Texts[len(lyr.Texts)-1] += ";" + line.strip()
					#print str( len(line.strip().split(" ")) ) + " : " + lyr.Texts[len(lyr.Texts)-1] + " : " + line.strip()
					#print str( len(line.strip().split(" ")) ) + " : " + lyr.Texts[len(lyr.Texts)-1]

				lyr.Contures.append(line.strip())				
			#kraj za layer				
			elif line.startswith("END_LAYER"):
				self.newLayers.append(lyr)			



			elif line.startswith("CONTROL "):
				strControlLayerDictName = self.FormatPrefix + line.replace(" ","_").strip().lower()
				arrControlLayerRecords_Nested = []
				arrControlLayerRecords_Surround = []
				arrArea = []


			elif line.startswith("CONTUR_AREA "):			
				#obrabotwam red za plosht na poligon
				#arrArea.append(line.replace("CONTUR_AREA ", "").strip())

				#arrArea.append(line.replace("CONTUR_AREA ", "").strip().split(' '))

				aarr = line.replace("CONTUR_AREA ", "").strip().split(' ')
				#aarr.insert(0, str(self.ImportID))

				#self.Area.append(dict(zip(['import_id', 'n', 'area'], aarr )) )
				self.Area.append(dict(zip(['n', 'area'], aarr )) )



			elif line.startswith("CONTUR_NESTED "):							
				#obrabotwam red za kontrol na layer
				arrControlLayerRecords_Nested.append(line.replace("CONTUR_NESTED ", "").strip())
			elif line.startswith("CONTUR_SURROUND "):			
				#obrabotwam red za kontrol na layer
				arrControlLayerRecords_Surround.append(line.replace("CONTUR_SURROUND ", "").strip())
			elif line.startswith("END_CONTROL"):	

				arrControlLayerDictKey_Nested.append(strControlLayerDictName)
				arrControlLayerDictValue_Nested.append(arrControlLayerRecords_Nested)				
				arrControlLayerDictKey_Surround.append(strControlLayerDictName)
				arrControlLayerDictValue_Surround.append(arrControlLayerRecords_Surround)



			elif line.startswith("TABLE "):			
				strTableDictName = self.FormatPrefix + line.replace(" ","_").strip().lower()
				arrTableRecords = []
				arrTableColumns = []
			elif line.startswith("F "):			
				#Dobawqm imenata na poletata w masiw
				arrTableColumns.append(line.split(" ")[1])
			elif line.startswith("D "):								
				#obrabotwam red za tablica
				arrTableRecords.append(line)				
			elif line.startswith("END_TABLE"):
				arrTableDictKey.append(strTableDictName)
				arrTableDictValueColumns.append(arrTableColumns)
				arrTableDictValueRecords.append(arrTableRecords)


		self.ControlLayers_Nested = dict( zip(arrControlLayerDictKey_Nested,arrControlLayerDictValue_Nested) )
		self.ControlLayers_Surround = dict( zip(arrControlLayerDictKey_Surround,arrControlLayerDictValue_Surround) )
		self.Tables = dict( zip(arrTableDictKey,arrTableDictValueRecords) )
		self.TablesColumns = dict( zip(arrTableDictKey,arrTableDictValueColumns) )




	def createAreaTable(self):
		#TODO trqbwa po-intelignentno dobawqne na import_id
		for e in self.Area:
			e['import_id'] = self.ImportID
		# tozi kod e wkaran incidentno za da syzdawa tablica s plo]ite		
		############
		#tableName = 'cz_control_area'
		tableName = "id_%s_control_area_tbl" % str(self.ImportID)

		xxx ='''id serial NOT NULL,
		layer_name character varying(256),'''

		columns = ['import_id', 'n', 'area']

		strKeysForTable = " varchar(250), ".join([col for col in columns])
		strKeys = ",".join([col for col in columns])
		strValues = ")s,%(".join([col for col in columns])
		strValues = "%(" + strValues + ")s"		

		c = self.db.cursor()
		c.execute("SELECT * FROM pg_class WHERE relname = '" + tableName.lower() + "'")
		if len(c.fetchall()) == 0:
			#c.execute("CREATE TABLE "+tableName+"( id serial NOT NULL, "+strKeysForTable+"  varchar(250))")
			c.execute("CREATE TABLE "+tableName+"( "+xxx+" "+strKeysForTable+"  varchar(250))")
		c.execute("set client_encoding to 'WIN'")
		c.executemany("""INSERT INTO """+tableName+"""("""+strKeys+""") VALUES("""+strValues+""")""", self.Area)		

		c.close()
		self.db.commit()		
		##########



	def LayersToPostGIS(self):
		#syzdawam tablica za greshkite
		self.__CreateServiceTables()
		#do tuk syzdawam tablica za greshkite			

		for lyr in self.newLayers:
			if not(lyr.Name.endswith("layer_shemi")):
				lyr.ImportPoints("_p")
				lyr.ImportSymbols("_s")
				lyr.ImportLines("_l")
				lyr.ImportContures("_c")


	def TableToPostGIS(self, _tableName):
		c = self.db.cursor()
		tableName = _tableName	
		tableNameForSQL = "id_" + str(self.ImportID) + "_" + _tableName + "_tbl"		

		strKeysForTable = " varchar(250),".join([col for col in self.TablesColumns[tableName]])
		strKeys = ",".join([col for col in self.TablesColumns[tableName]])
		strValues = ")s,%(".join([col for col in self.TablesColumns[tableName]])
		strValues = "%(" + strValues + ")s"
		#Dobawqm pole za EKATTE, s promeneno ima zaradi syshtestwuwashto pole
		strKeys = "import_id," + strKeys
		strValues = "%(import_id)s," + strValues
		strKeysForTable = "import_id varchar(30)," + strKeysForTable

		c.execute("SELECT * FROM pg_class WHERE relname = '" + tableNameForSQL + "'")
		if len(c.fetchall()) == 0:					
			c.execute("CREATE TABLE " + tableNameForSQL + "( id serial NOT NULL, "+strKeysForTable+" varchar(250))")		

		c.execute("set client_encoding to 'WIN'")		

		dictTmp = self.listToDictForTables(self.Tables[tableName], strKeys)
		#c.executemany("""INSERT INTO """+tableName+"""("""+strKeys+""") VALUES(%("""+strValues+""")s)""", dictTmp)
		c.executemany("""INSERT INTO """ + tableNameForSQL + """("""+strKeys+""") VALUES("""+strValues+""")""", dictTmp)



		c.close()
		self.db.commit()

	def TablesToPostGIS(self):
		for tbl in self.TablesColumns:
			self.TableToPostGIS(tbl)						



	def listToDictForTexts(self, _list, _arrKeys):	
		arrKeys = _arrKeys
		arrValues = []
		listTmp = []

		for item in _list:
			strItem = item.strip()			
			arrValues = strItem.split(";")
			part1 = arrValues[0].strip()
			if len(arrValues)==2:
				part2 = arrValues[1].strip()

				arr1 = part1.split(" ")
				arr2 = part2.split(" ")

				arrValues = arr1
				if part2.startswith("C "):
					arrValues = arr1 + arr2
				else:
					arrValues.append(part2)
			else:	
				arr1 = part1.split(" ")
				arrValues = arr1

			if len(arrValues) <= len(arrKeys) - 2: #Magic
				razlika = (len(arrKeys) - len(arrValues)) - 2 #Magic
				for i in range(razlika):
					#insyrtwane na tretposlednomqsto
					arrValues.insert(len(arrValues)-1,"")


				x = self.RefX + float(arrValues[magic3]) #Magic!!!3
				y = self.RefY + float(arrValues[magic4]) #Magic!!!4
				arrValues.append("POINT(" + str(y) + " " + str(x) + ")")
				arrValues.insert(0, self.ImportID) #wmykwam stojnost za IMPORT_ID - w pole IMPORT_ID
				arrValues.insert(1, "ttttt") #wmykwam stojnost layer_name

				dictTemp = dict( zip(arrKeys,arrValues) )
				listTmp.append(dictTemp)
			else:
				print "neeeeeeeeee"
				logging.debug( "neeeeeeeeee" )


		return listTmp




	def listToDictForTables(self, _list, _keys):
		arrKeys = _keys.split(",")
		arrValues = []
		arrResult = []

		c = self.db.cursor()
		for item in _list:
			strValues = item
			strValues = strValues.replace("D ", "")
			strValues = strValues.strip()

			#коментар за коректно вкарване на ZEMIMOTI
			#tglValues = strValues.split(",")
			#for el in tglValues:
			#    if el == ' 5 ':
	#		el = '050'
	#	    elif el == '5  ':
	#		el = '500'
	#	    
			strValues = strValues.replace(", ", ",")
			strValues = strValues.replace(" ,", ",")
			arrValues = strValues.split(",")
			#arrValues.insert(0, self.EKATTE) #wmykwam stojnost za EKKATE - w pole EKT
			#arrValues.insert(0, self.ImportTime) #wmykwam stojnost za EKKATE - w pole EKT
			#arrValues.insert(0, self.czFileName) #wmykwam stojnost za EKKATE - w pole EKT
			arrValues.insert(0, self.ImportID) #wmykwam stojnost za IMPORT_ID - w pole IMPORT_ID


			if len(arrKeys) == len(arrValues):
				dictTemp = dict( zip(arrKeys,arrValues) )
				arrResult.append(dictTemp)
			else:	
				# izrazwam poslednite elementi, trqbwa po-dobro reshenie:
				razlika = len(arrValues) - len(arrKeys)
				if razlika > 0:
					for i in range(razlika):
						arrValues.remove(arrValues[len(arrValues)-1])
				elif razlika < 0:				    
					for i in range(abs(razlika)):		# dopylwam s prazni stojnosti ako kluchowete sa poweche ot stojnostite			
						arrValues.append("") #dobawqm  na posledno mqsto

				if len(arrKeys) == len(arrValues):
					dictTemp = dict( zip(arrKeys,arrValues) )
					arrResult.append(dictTemp)
				else:	
					print "Problem:\tValues: "+str(len(arrValues))+"\tKeys: "+str(len(arrKeys))
					logging.debug( "Problem:\tValues: "+str(len(arrValues))+"\tKeys: "+str(len(arrKeys)) )
					#c.execute("""INSERT INTO cz_error (table_name,error_record) VALUES("""+arrValues[0]+""","""+arrValues[0]+""")""")

			#arrResult.append(dictTemp)
		return arrResult


	def Stats(self):
		for tbl in self.Tables:
			print tbl + "\n\tFields count: " + str(len(self.TablesColumns[tbl]))
			print "\tRecords count: " + str(len(self.Tables[tbl]))
			logging.debug( tbl + "\n\tFields count: " + str(len(self.TablesColumns[tbl])) )
			logging.debug( "\tRecords count: " + str(len(self.Tables[tbl])) )





# PUBLIC METHODS
	def ImportFile(self):
		self.PrepareFile()
		self.FillLayersAndTablesFromPreparedFile()


		#self.LayersToPostGIS() # ili moje da se wikat pootdelno za widowe obekti:
		self.__CreateServiceTables()
		for lyr in self.newLayers:
			#lyr.FeaturesToOGR("_p")
			if not(lyr.Name.endswith("layer_shemi")):
				lyr.ImportFeaturesToBD("_t")				
				lyr.ImportFeaturesToBD("_p")
				lyr.ImportFeaturesToBD("_s")
				lyr.ImportFeaturesToBD("_l")
				lyr.ImportFeaturesToBD("_c")
				lyr.ImportFeaturesToBD("_i")


		self.TablesToPostGIS()
		self.createAreaTable()
	#	self.Stats()
		#self.Sumarize("cz_result_02", "id_%_id")
		self.Sumarize("cz_pnts_p_cad_" + self.Zone1970, "id_" + str(self.ImportID) + "%_cadaster_p_id")
		self.Sumarize("cz_pnts_s_cad_" + self.Zone1970, "id_" + str(self.ImportID) + "%_cadaster_s_id")
		self.Sumarize("cz_pnts_t_cad_" + self.Zone1970, "id_" + str(self.ImportID) + "%_cadaster_t_id")
		self.Sumarize("cz_lins_cad_" + self.Zone1970, "id_" + str(self.ImportID) + "%_cadaster_l_id")
		self.Sumarize("cz_polys_cad_" + self.Zone1970, "id_" + str(self.ImportID) + "%_cadaster_c_id")
		self.Sumarize("cz_innerpnts_cad_" + self.Zone1970, "id_" + str(self.ImportID) + "%_cadaster_i_id")

		self.Sumarize("cz_pnts_p_leso_" + self.Zone1970, "id_" + str(self.ImportID) + "%_leso_p_id")
		self.Sumarize("cz_pnts_s_leso_" + self.Zone1970, "id_" + str(self.ImportID) + "%_leso_s_id")
		self.Sumarize("cz_pnts_t_leso_" + self.Zone1970, "id_" + str(self.ImportID) + "%_leso_t_id")
		self.Sumarize("cz_lins_leso_" + self.Zone1970, "id_" + str(self.ImportID) + "%_leso_l_id")
		self.Sumarize("cz_polys_leso_" + self.Zone1970, "id_" + str(self.ImportID) + "%_leso_c_id")
		self.Sumarize("cz_innerpnts_leso_" + self.Zone1970, "id_" + str(self.ImportID) + "%_leso_i_id")



		self.Sumarize("cz_pnts_p_regplan_" + self.Zone1970, "id_" + str(self.ImportID) + "%_regplan_p_id")
		self.Sumarize("cz_pnts_s_regplan_" + self.Zone1970, "id_" + str(self.ImportID) + "%_regplan_s_id")
		self.Sumarize("cz_pnts_t_regplan_" + self.Zone1970, "id_" + str(self.ImportID) + "%_regplan_t_id")
		self.Sumarize("cz_lins_regplan_" + self.Zone1970, "id_" + str(self.ImportID) + "%_regplan_l_id")
		self.Sumarize("cz_polys_regplan_" + self.Zone1970, "id_" + str(self.ImportID) + "%_regplan_c_id")
		self.Sumarize("cz_innerpnts_regplan_" + self.Zone1970, "id_" + str(self.ImportID) + "%_regplan_i_id")



		#self.Sumarize("cz_tables", "id_" + str(self.ImportID) + "%_tbl")	

		self.Sumarize("cz_table_acts", "id_" + str(self.ImportID) +"%table_acts%_tbl")
		self.Sumarize("cz_table_address", "id_" + str(self.ImportID) +"%table_address%_tbl")
		self.Sumarize("cz_table_aparts", "id_" + str(self.ImportID) +"%table_aparts%_tbl")
		self.Sumarize("cz_table_cadrajon", "id_" + str(self.ImportID) +"%table_cadrajon%_tbl")
		self.Sumarize("cz_table_docs", "id_" + str(self.ImportID) +"%table_docs%_tbl")
		self.Sumarize("cz_table_doctype", "id_" + str(self.ImportID) +"%table_doctype%_tbl")
		self.Sumarize("cz_table_dogovori", "id_" + str(self.ImportID) +"%table_dogovori%_tbl")
		self.Sumarize("cz_table_gorimoti", "id_" + str(self.ImportID) +"%table_gorimoti%_tbl")
		self.Sumarize("cz_table_history", "id_" + str(self.ImportID) +"%table_history%_tbl")
		self.Sumarize("cz_table_imoti", "id_" + str(self.ImportID) +"%table_imoti%_tbl")
		self.Sumarize("cz_table_ipoteki", "id_" + str(self.ImportID) +"%table_ipoteki%_tbl")
		self.Sumarize("cz_table_izdateli", "id_" + str(self.ImportID) +"%table_izdateli%_tbl")
		self.Sumarize("cz_table_mestnosti", "id_" + str(self.ImportID) +"%table_mestnosti%_tbl")
		self.Sumarize("cz_table_niskiniva", "id_" + str(self.ImportID) +"%table_niskiniva%_tbl")
		self.Sumarize("cz_table_ogr", "id_" + str(self.ImportID) +"%table_ogr%_tbl")
		self.Sumarize("cz_table_ogrpimo", "id_" + str(self.ImportID) +"%table_ogrpimo%_tbl")
		self.Sumarize("cz_table_operatori", "id_" + str(self.ImportID) +"%table_operatori%_tbl")
		self.Sumarize("cz_table_otregdane", "id_" + str(self.ImportID) +"%table_otregdane%_tbl")
		self.Sumarize("cz_table_persons", "id_" + str(self.ImportID) +"%table_persons%_tbl")
		
		self.Sumarize("cz_table_pozemlimoti", "id_" + str(self.ImportID) +"%table_pozeml%_tbl")
		self.Sumarize("cz_table_prava", "id_" + str(self.ImportID) +"%table_prava%_tbl")
		self.Sumarize("cz_table_primesta", "id_" + str(self.ImportID) +"%table_primesta%_tbl")
		self.Sumarize("cz_table_promeni", "id_" + str(self.ImportID) +"%table_promeni%_tbl")
		self.Sumarize("cz_table_protocol", "id_" + str(self.ImportID) +"%table_protocol%_tbl")
		self.Sumarize("cz_table_regconturi", "id_" + str(self.ImportID) +"%table_regconturi%_tbl")
		self.Sumarize("cz_table_remarks", "id_" + str(self.ImportID) +"%table_remarks%_tbl")
		self.Sumarize("cz_table_restrictions", "id_" + str(self.ImportID) +"%table_restrictions%_tbl")
		self.Sumarize("cz_table_serv", "id_" + str(self.ImportID) +"%table_serv%_tbl")
		self.Sumarize("cz_table_servituti", "id_" + str(self.ImportID) +"%table_servituti%_tbl")
		self.Sumarize("cz_table_sgradi", "id_" + str(self.ImportID) +"%table_sgradi%_tbl")
		self.Sumarize("cz_table_skici", "id_" + str(self.ImportID) +"%table_skici%_tbl")
		self.Sumarize("cz_table_sobstvenost", "id_" + str(self.ImportID) +"%table_sobstvenost%_tbl")
		self.Sumarize("cz_table_tejesti", "id_" + str(self.ImportID) +"%table_tejesti%_tbl")
		self.Sumarize("cz_table_ulic", "id_" + str(self.ImportID) +"%table_ulic%_tbl")
		self.Sumarize("cz_table_zapodobr", "id_" + str(self.ImportID) +"%table_zapodobr%_tbl")
		self.Sumarize("cz_table_zapovedi", "id_" + str(self.ImportID) +"%table_zapovedi%_tbl")
		self.Sumarize("cz_table_zemimoti", "id_" + str(self.ImportID) +"%table_zemimoti%_tbl")

		self.Sumarize("cz_table_podotdeli1", "id_" + str(self.ImportID) +"%table_podotdeli1%_tbl")
		self.Sumarize("cz_table_podotdeli", "id_" + str(self.ImportID) +"%table_podotdeli%_tbl")
		
		
		self.Sumarize("cz_table_composite", "id_" + str(self.ImportID) +"%table_composite%_tbl")
		self.Sumarize("cz_table_sections", "id_" + str(self.ImportID) +"%table_sections%_tbl")
		self.Sumarize("cz_table_woodtype", "id_" + str(self.ImportID) +"%table_woodtype%_tbl")



		self.Sumarize("cz_table_imotkateg", "id_" + str(self.ImportID) +"%table_imotkateg%_tbl")

		self.Sumarize("cz_control_area", "id_" + str(self.ImportID) +"%_control_area%_tbl")



		#self.Sumarize("cz_result_layer", "id_" + str(self.ImportID) + "%_id")	
		#self.Sumarize("cz_result_table", "id_" + str(self.ImportID) + "%_tbl")	




# END PUBLIC METHODS	

class czImport():    		
	def __init__ (self, czFileOrFolderName, db):
		self.db = db
		self.czFileOrFolderName = czFileOrFolderName

	def ImportFileOrFolder(self, _recursive = False):	
		if os.path.isfile(self.czFileOrFolderName):
			self.ImportFile(self.czFileOrFolderName)
		elif os.path.isdir(self.czFileOrFolderName):
			self.ImportFolder(_recursive)
		else:
			print "NOT FILE OR FOLDER"

#блок който пълни служебните таблизи за точки и линии за последваща проверка
#tmpCad.FillContureLineTable = False - не пълни таблицата
#tmpCad.FillContureLineTable = True - пълни таблицата
#tmpCad.FillLinePointTable = False - не пълни таблицата
#tmpCad.FillLinePointTable = True - пълни таблицата
	def ImportFile(self, _fileName):
		tmpCad = czFileHandler(czFullFileName = _fileName, db = self.db)
		tmpCad.FillContureLineTable = False # pylni slujebnata tablica za izsledwaniq na greshkite
		tmpCad.FillLinePointTable = False # pylni slujebnata tablica za izsledwaniq na greshkite
		tmpCad.ImportFile()

	def ImportFolder(self, _recursive = False):
		if not _recursive:
			for fileName in os.listdir (self.czFileOrFolderName):
				fullFileName = os.path.join(self.czFileOrFolderName, fileName)
				if fullFileName.lower().endswith(".zem") or fullFileName.lower().endswith(".cad"):
					try:
						self.ImportFile(fullFileName)
					except:    
						print "LOOP ERROR:\t" + fullFileName  			
		else:
			for root, dirs, files in os.walk(self.czFileOrFolderName):
				for fileName in [f for f in files if f.lower().endswith(".zem") or f.lower().endswith(".cad")]:
					fullFileName = os.path.join(root, fileName)
					try:
						self.ImportFile(fullFileName)
					except:    
						print "LOOP ERROR REC:\t" + fullFileName  			




if __name__ == "__main__":
	import sys

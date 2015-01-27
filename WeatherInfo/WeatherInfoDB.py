__author__ = 'ap'

#!/usr/bin/env python

import os, sys, time, re
import datetime
import sqlite3

# http://docs.python.org/release/2.6/library/sqlite3.html
# http://www.sqlite.org/docs.html
# http://www.sqlite.org/lang_datefunc.html
# http://www.sqlite.org/datatype3.html

class WeatherInfoDB(object):
	"""docstring for WeatherInfoDB"""

	def __init__(self, location=None,dbName='weatherInfoDB_new.sql3'):
		super(WeatherInfoDB, self).__init__()

		self.dbPath = '../db/'
		if not os.path.exists(self.dbPath):
			os.makedirs(self.dbPath)

		if not location:
		    print "ERROR: location not specified !! "
		    sys.exit(-1)

		self.dbName = dbName
		self.conn = sqlite3.connect(self.dbPath+self.dbName)

		self.location = location
		# print "location set to ", self.location

		self.tableName = 'WeatherInfoWeb'

		self.start = time.time()
		self.lastStamp = 9999999999


	def setLocation(self, newLocation):
		self.location = newLocation
		# print 'location reset to ', self.location

	def __del__(self):
		"""docstring for __del__"""

		# make sure all open things are committed:
		self.conn.commit()
		self.conn.close()

	def createTable(self):
		"""docstring for createDB"""
		# get a cursor from the DB
		c = self.conn.cursor()
		# Create table
		c.execute('''create table %s
		(stamp text, location text, windDir integer, windSpeed integer, temp integer, dew integer, qnh integer, gustSpeed integer)
		''' % self.tableName )
		# Save (commit) the changes
		self.conn.commit()
		# We can also close the cursor if we are done with it
		c.close()
		print "table ", self.tableName, ' created in ', self.dbPath+self.dbName

	def parseLineAndFillDB(self, line, infoRe, cursor):

		infoMatch = infoRe.match(line)
		if not infoMatch:
			print "no match found for '"+line+"'"
			print '   when checking   ', infoRe.pattern
			return False
		else:
			today = datetime.datetime.fromtimestamp( time.time() )
			yr0  = today.year
			mon0 = today.month
			items = list( infoMatch.groups() )
			if 'VRB' in items[5]:
				items[5] = items[5].replace('VRB','000')

			# print line
			# print items
			if items[7] == None : items[7] = '-1'  # in case there were no Gusts ...
			items[7] = items[7].replace('G','')

			yr, mon, day, hr, min, windDir, windSpeed, windGst, temp, dew, qnh = [int(x.replace('M','-')) for x in items]
			# print items[0],items[1],items[2], day, hr, min, datetime.datetime(yr, mon, day, hr, min, 00)
			# if mon > mon0:
			# 	print "WOULD DO : resetting month as seen in file ", mon, ' to current month ', mon0

			# fix the "confusion" on the last hour of a month:
			# check if the next month _has_ this day (e.g. the 29/30/31 of Feb don't exist)
			try:
			    stampSec = time.mktime( datetime.datetime(yr, mon, day, hr, min, 00).timetuple() )
			except ValueError, e:
			    if "day is out of range for month" in str(e):
			        print "found month out of range, using ", mon-1
			        stampSec = time.mktime( datetime.datetime(yr, mon-1, day, hr, min, 00).timetuple() )
			    else:
			        raise e
			except:
			    raise

			# now we have the stamp, check if it's in the future (e.g. points to March 28 on Feb 28)
			if (time.time() - stampSec) < 0 :
			    print "fixing time stamp in future ... "
			    stampSec = time.mktime( datetime.datetime(yr, mon-1, day, hr, min, 00).timetuple() )

			stamp = (self.start - stampSec )

			if abs(stamp - self.lastStamp) > 900: # make sure at least 15 have passed
				# print 'updating for ', stamp, self.lastStamp, qnh, datetime.datetime(yr, mon, day, hr, min, 00)
				self.lastStamp = stamp
				t = (datetime.datetime.fromtimestamp(stampSec), self.location, windDir, windSpeed, temp, dew, qnh, windGst)
				cursor.execute('insert into '+self.tableName+' values (?,?,?,?,?,?,?,?)', t)
				# print "updated DB with ", t

		return True

	def parseLineAndUpdateGusts(self, line, infoRe, cursor):

		infoMatch = infoRe.match(line)
		if not infoMatch:
			print "no match found for '"+line+"'"
			print '   when checking   ', infoRe.pattern
			return False
		else:
			today = datetime.datetime.fromtimestamp( time.time() )
			yr0  = today.year
			mon0 = today.month
			items = list( infoMatch.groups() )
			if 'VRB' in items[5]:
				items[5] = items[5].replace('VRB','000')

			# print line
			# print items
			if items[7] == None : items[7] = '-1'  # in case there were no Gusts ...
			items[7] = items[7].replace('G','')

			yr, mon, day, hr, min, windDir, windSpeed, windGst, temp, dew, qnh = [int(x.replace('M','-')) for x in items]
			# print items[0],items[1],items[2], day, hr, min, datetime.datetime(yr, mon, day, hr, min, 00)

			if windGst < 0: return True

			try:
				stampSec = time.mktime( datetime.datetime(yr, mon, day, hr, min, 00).timetuple() )
			except ValueError, e:
				if "day is out of range for month" in str(e):
					print "found out of range day: ", day, mon
					stampSec = time.mktime( datetime.datetime(yr, mon-1, day, hr, min, 00).timetuple() )

			stamp = (self.start - stampSec )

			cmd = 'update '+self.tableName+' set gustSpeed=%i where stamp = "%s" and location = "%s" ;' %(windGst, datetime.datetime.fromtimestamp(stampSec), self.location)
			# print cmd
			cursor.execute(cmd)
			# print "updated DB with ", t

		return True


	def fillDB(self):

		location = self.location
		ICAOLocationIndicators = { 'gva' : 'LSGG',
								   'skg' : 'LGTS'}

		dataFile = open('/Users/ap/various/'+location+'-weather-web.list-yrmo', 'r')
		infoRe = re.compile(ICAOLocationIndicators[location]+' (\d\d\d\d)(\d\d)(\d\d)(\d\d)(\d\d)Z ([V\d][R\d][B\d])(\d+)(G\d+)?KT .* (M?\d\d)\/(M?\d\d) Q(\d+)\s*.*')

		cursor = self.conn.cursor()
		for line in dataFile.readlines():
			if not self.parseLineAndFillDB(line, infoRe, cursor):
				print "ERROR parsing: ", line[:-1]

		self.conn.commit()
		cursor.close()

		return

	def checkTableInDB(self):
		"""docstring for checkTableInDB"""

		if not self.tableName : return True

		# WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%'

		query = """
		SELECT name FROM sqlite_master
		WHERE type IN ('table','view')
		UNION ALL
		SELECT name FROM sqlite_temp_master
		WHERE type IN ('table','view')
		ORDER BY 1
		"""
		c = self.conn.cursor()
		c.execute(query)
		tableFound = False
		for row in c:
			# print row
			if self.tableName in row: tableFound = True
		c.close()

		return tableFound

	def updateDB(self):
		"""docstring for updateDB"""
		if not self.checkTableInDB():
			self.createTable()
			print "table ",self.tableName,'created.'

		self.fillDB()

		# c = self.conn.cursor()
		# c.execute('select * from '+self.tableName)
		# print "table ",self.tableName,'has now',len(c.fetchall()),'rows.'

	def updateGusts(self):

		if not self.checkTableInDB():
			print 'ERROR: cannot update gusts on empty DB'
			sys.exit(-1)

		location = self.location
		ICAOLocationIndicators = { 'gva' : 'LSGG',
								   'skg' : 'LGTS'}

		dataFile = open('/Users/ap/various/'+location+'-weather-web.list-yrmo', 'r')
		infoRe = re.compile(ICAOLocationIndicators[location]+' (\d\d\d\d)(\d\d)(\d\d)(\d\d)(\d\d)Z ([V\d][R\d][B\d])(\d+)(G\d+)?KT .* (M?\d\d)\/(M?\d\d) Q(\d+)\s*.*')

		cursor = self.conn.cursor()
		for line in dataFile.readlines():
			if not self.parseLineAndUpdateGusts(line, infoRe, cursor):
				print "ERROR parsing: ", line[:-1]

		self.conn.commit()
		cursor.close()

		return


	def readDB(self, location, what=['temp','qnh'], since='7'):
		"""this method should be overwritten by the reader class ..."""
        pass


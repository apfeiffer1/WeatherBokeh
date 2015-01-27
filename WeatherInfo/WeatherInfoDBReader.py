
__author__ = 'Andreas Pfeiffer'
__email__  = 'apfeiffer1@gmail.com'


from WeatherInfoDB import WeatherInfoDB

class WeatherInfoDBReader(WeatherInfoDB):
    """docstring for WeatherInfoDBReader"""
    def __init__(self, loc):
        super(WeatherInfoDBReader, self).__init__(loc)

    # overwrite inherited class
    def readDB(self, location, what=['temp','qnh'], since='7'):
        """docstring for readDB"""

        c = self.conn.cursor()
        results = { 'date' : [] }
        for item in what:
            results[item] = []

        query = 'select datetime(stamp),'+','.join(what)+' from '+self.tableName
        query += ' where ( '
        query += ' datetime(stamp) > datetime("now","-'+since+' day") '
        query += ' and location like "'+location+'" '
        query += ')'  # end where (
        c.execute(query)
        for row in c:
            results['date'].append( row[0].replace(' ', 'T') )
            i = 0
            for item in what:
                i += 1
                results[item].append( float(row[i]) )

        return results

    def minMax(self, location, what=['temp','qnh'], since='7'):
        """docstring for minMax"""

        c = self.conn.cursor()
        results = {}
        results['min'] = {}
        for item in what:
            query = 'select min('+item+') from '+self.tableName
            query += ' where ( '
            query += ' datetime(stamp) > datetime("now","-'+since+' day") '
            query += ' and location like "'+location+'" '
            query += ')'  # end where (
            c.execute(query)
            values = []
            for row in c:
                if row == (None,):  # take care of "no data found"
                    values.append( -1. )
                    continue
                try:
                    values.append( float(row[0]) )
                except:
                    print "row is:", row
                    raise
            results['min'][item] = values[0]

        results['max'] = {}
        for item in what:
            query = 'select max('+item+') from '+self.tableName
            query += ' where ( '
            query += ' datetime(stamp) > datetime("now","-'+since+' day") '
            query += ' and location like "'+location+'" '
            query += ')'  # end where (
            c.execute(query)
            values = []
            for row in c:
                if row == (None,):   # take care of "no data found"
                    values.append( -1. )
                    continue
                values.append( float(row[0]) )
            results['max'][item] = values[0]

        return results

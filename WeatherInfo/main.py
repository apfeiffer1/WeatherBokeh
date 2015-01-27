__author__ = 'ap'

import numpy as np

from bokeh.plotting import figure, show
from bokeh.models import Range1d

from bokeh.resources import CDN
from bokeh.embed import components

from WeatherInfoDBReader import WeatherInfoDBReader

since = '4'

def readData(loc, since=since):
    widb = WeatherInfoDBReader(loc)
    items = ['temp','qnh','windSpeed','windDir','gustSpeed']
    resJson = widb.readDB(loc, items, since=since)
    return resJson

def getMinMax(loc, since=since):
    widb = WeatherInfoDBReader(loc)
    items = ['temp','qnh','windSpeed','windDir','gustSpeed']
    resJson = widb.minMax(loc, items, since=since)
    return resJson

def showOne(locDataIn, loc='gva', what='temp', col='red'):
    locData = locDataIn[loc]

    whatIn = what
    if whatIn == 'qnh' : whatIn = 'pressure'

    p1 = figure(x_axis_type = "datetime", plot_width=400, plot_height=200,)
    p1.line( np.array(locData['date'], dtype='datetime64[s]'), np.array(locData[what]),
     color=col, linewidth=3, legend=whatIn.capitalize())
    if what == 'windSpeed': # add also gust information
        p1.rect( np.array(locData['date'], dtype='datetime64[s]'),
                 np.array(locData['gustSpeed']),
                 [1] * len(np.array(locData['date'], dtype='datetime64[s]')),
                 [1] * len(np.array(locData['date'], dtype='datetime64[s]')),
                 color='blue', linewidth=3, legend='gusts')
        ymax = max(np.array(locData['gustSpeed']))
        if ymax < 0 : # no gusts in range, use max from windspeed:
            ymax = max(np.array(locData['windSpeed']))
        p1.y_range = Range1d(start=0, end=ymax*1.2)
    p1.title = "%s (%s)" % (whatIn, loc)
    p1.grid.grid_line_alpha=0.3
    p1.legend.orientation = "top_left"
    return components(p1, CDN)

class Plot(object):
    pass

def makePlots(locData):

    plots = {}
    for loc in ['gva']:
        plots[loc] = []
        plot = Plot()
        plot.script, plot.div = showOne(locData, loc=loc, what='temp')
        plots[loc].append(plot)

        plot = Plot()
        plot.script, plot.div = showOne(locData, loc=loc, what='qnh', col='blue')
        plots[loc].append(plot)

        plot = Plot()
        plot.script, plot.div = showOne(locData, loc=loc, what='windSpeed', col='green')
        plots[loc].append(plot)

        plot = Plot()
        plot.script, plot.div = showOne(locData, loc=loc, what='windDir', col='green')
        plots[loc].append(plot)

    return plots

class Info(object):
    pass

def findActualData(locData):
    actualData = {}

    for loc in ['gva']:
        info = Info()
        info.temp = locData[loc]['temp'][-1]
        info.qnh  = locData[loc]['qnh'][-1]
        info.windSpeed = locData[loc]['windSpeed'][-1]
        info.gustSpeed = locData[loc]['gustSpeed'][-1]
        info.lastUpdate = locData[loc]['date'][-1]
        actualData[loc] = info

    return actualData
# ---------------------------------------------------------------------------------------------------

from flask import Flask, render_template
app = Flask(__name__)

@app.route("/")
def show():
    minMax = {}
    minMax['gva'] = getMinMax('gva', since=since)

    locData = {}
    locData['gva'] = readData('GVA')

    actualData = findActualData(locData)

    plots = makePlots(locData)
    return render_template('weatherInfo.html', plots=plots, actualData=actualData, minMax=minMax)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')


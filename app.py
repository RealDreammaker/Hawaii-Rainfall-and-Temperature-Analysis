# Import dependancies
from flask import Flask, jsonify
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import numpy as np

#################################################
# Setup database
#################################################
# create engine to hawaii.sqlite
engine = create_engine("sqlite:///./Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect = True)

# View all of the classes that automap found
Base.classes.keys()

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# define function to convert date from mm-dd-yyyy format to sql default date format
def date_converter(strdate):
    td = dt.datetime.strptime(strdate, '%m-%d-%Y')
    return dt.date(td.year, td.month, td.day)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

@app.route('/')
def home():
    """Home page"""
    start = "start"
    end = "end"
    return (f"Welcome to Climate App! <br/>"
           f"-----------------------<br/>"
           f"Available routes (add to home route): <br/>"
           f"- Display all precipitation:           /api/v1.0/precipitation<br/>"
           f"- Display all stations:                /api/v1.0/stations<br/>"
           f"- Temperature observations of <br/>"
           f"the most active station one year ago   /api/v1.0/tobs<br/>"
           f"- Find the min,max,average temperature <br/>"
           f"given the start date                   /api/v1.0/< startdate ><br/>"
           f"- Find the min,max,average temperature <br/>"
           f"given the start date and end date      /api/v1.0/< startdate >/< enddate > <br/>"
           f"-----------------------<br/>"
           f"<br/>"
           f"Date format: M-D-YYYY")

@app.route('/api/v1.0/precipitation')
def precipitation():
    """Display all precipitation"""
    # Create our session (link) from Python to the DB
    session = Session(engine)
    results = session.query(Measurement.date, Measurement.prcp).all()
    session.close()
        
    # data cleaning / removing null values, create a dictionary variable
    precipitation = []
    for date, prcp in results:
        if type(prcp) == float:
            dict_var = {}
            dict_var['Date'] = date
            dict_var['precipitation'] = prcp
            precipitation.append(dict_var)
    
    return jsonify(precipitation)
        
@app.route('/api/v1.0/stations')
def stations():
    """Display all stations"""
    # Create our session (link) from Python to the DB
    session = Session(engine)
    results = session.query(Measurement.station, Station.name).\
               filter(Measurement.station == Station.station).\
                distinct().all()
    session.close()  
    
    stations = []
    for station_id, station_name in results:
        dict_var = {}
        dict_var['Station ID'] = station_id
        dict_var['Station name'] = station_name
        stations.append(dict_var)
    
    return jsonify(stations)
        
@app.route('/api/v1.0/tobs')
def tobs():        
    """Temperature observations of the most active station one year ago"""   
    most_active_station = 'USC00519281'
    recent_date = dt.date(2017,8,23)
    start_date = recent_date - dt.timedelta(days = 365) 
    
    session = Session(engine)
    results  = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station).\
        filter(Measurement.date >= start_date).all()
    session.close()  
    
    temperature = []
    for date, temp in results:
        dict_var = {}
        dict_var['Date'] = date
        dict_var['TOBS'] = temp
        temperature.append(dict_var)
        
    return jsonify(temperature)
    

@app.route('/api/v1.0/<start>', defaults = {'end' : None})
@app.route('/api/v1.0/<start>/<end>')
def start_end(start, end=None):           
    """When given the start only, calculate TMIN, TAVG, and TMAX for all dates greater than and equal to the start date.

When given the start and the end date, calculate the TMIN, TAVG, and TMAX for dates between the start and end date inclusive."""
    # convert string given to date
    start_date = date_converter(start)
    if end is not None:
        end_date = date_converter(end)
    
    # assigning variables, getting ready for query
    lowest_temp = func.min(Measurement.tobs)
    highest_temp = func.max(Measurement.tobs)
    average_temp = func.round(func.avg(Measurement.tobs),2)
    loop = [lowest_temp, highest_temp, average_temp]
    labels = ["TMIN" , "TMAX", "TAVG"]
    output = {}
    
    # initiate session for query data from table
    session = Session(engine)
    
    
    for item in loop:
        # if no end date provided in the route, perform first query
        if end is not None:
            result = session.query(item).\
                filter(Measurement.date >= start_date).\
                filter(Measurement.date <= end_date).all()
        else:
            result = session.query(item).\
                filter(Measurement.date >= start_date).all()
            
        # add TMIN/TMAX/TAVG to the dictionary
        output[labels[loop.index(item)]] = result[0][0]
    
  
    session.close() 
    
    return jsonify(output)   

if __name__ == "__main__":
    app.run(debug = True)
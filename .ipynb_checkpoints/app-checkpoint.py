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
    return (f"Welcome to Climate App<br/>"
           f"-----------------------<br/>"
           f"Available routes: <br/>"
           f"/api/v1.0/precipitation<br/>"
           f"/api/v1.0/stations<br/>"
           f"/api/v1.0/tobs<br/>"
           f"/api/v1.0/< startdate ><br/>"
           f"/api/v1.0/< startdate >/< enddate >"
           f"<br/>"
           f"Date format: MM-DD-YYYY")

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
    """Temperature observations of the most active station for the last year of data"""   
    most_active_station = 'USC00519281'
    recent_date = dt.datetime(2017,8,23)
    start_date = recent_date - dt.timedelta(days = 366) 
    
    session = Session(engine)
    results  = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station).\
        filter(Measurement.date > start_date).all()
    session.close()  
    
    temperature = []
    for date, temp in results:
        dict_var = {}
        dict_var['Date'] = date
        dict_var['TOBS'] = temp
        temperature.append(dict_var)
        
    return jsonify(temperature)
    
@app.route('/api/v1.0/<start>')
def start(start):
    """calculate TMIN, TAVG, and TMAX for all dates greater than and equal to the start date."""
    # convert string given to date
    start_date = dt.datetime.strptime(start, '%m-%d-%Y') - dt.timedelta(days = 1)
    
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
        result = session.query(item).\
            filter(Measurement.date > start_date).all()
        
        # add TMIN/TMAX/TAVG to the dictionary
        output[labels[loop.index(item)]] = result[0][0]
        
    session.close()       
    return jsonify(output)        

@app.route('/api/v1.0/<start>/<end>')
def start_end(start, end):           
    """calculate TMIN, TAVG, and TMAX for dates between the start and end date inclusively"""
    # convert string given to date
    start_date = dt.datetime.strptime(start, '%m-%d-%Y') - dt.timedelta(days = 1)
    end_date = dt.datetime.strptime(end, '%m-%d-%Y')
    
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
        result = session.query(item).\
            filter(Measurement.date > start_date).\
            filter(Measurement.date <= end_date).all()
        
        # add TMIN/TMAX/TAVG to the dictionary
        output[labels[loop.index(item)]] = result[0][0]
    
    # add query details          
    output["3. Number of Observations"] = len(session.query(Measurement.date).\
            filter(Measurement.date > start_date).\
            filter(Measurement.date <= end_date).all())
         
    output["1. Start date"] = start
    output["2. End date"] = end
    
    session.close() 
    
    return jsonify(output)        


if __name__ == "__main__":
    app.run(debug = True)
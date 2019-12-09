# Import Modules
from __future__ import print_function
import os
import sys
import json
import pytz
import pyodbc
import logging
import azure.functions as func
from datetime import datetime

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Azure Function, Lafferty-Tracking, processed a request via HTTP Trigger.')

    # Parse parameters. Parameters can be passed in either query string or request body
    action = req.params.get('action')
    amount = req.params.get('amount')
    if not action:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            action = req_body.get('action')

    if not amount:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            amount = req_body.get('amount')

    if not action:
        return func.HttpResponse(
            "Please pass an [action] name and [amount] value on the query string or in the request body",
            status_code=400
        )
        sys.exit()
    
    if not amount:
        return func.HttpResponse(
            "Please pass an [action] name and [amount] value on the query string or in the request body",
            status_code=400
        )
        sys.exit()

    # Connect to SQL DB
    try:
        sqlConnStr = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server}; SERVER='+os.environ['db_server']+'; DATABASE='+os.environ['db']+'; UID='+os.environ['db_username']+'; PWD='+os.environ['db_password'])
        cursor = sqlConnStr.cursor()
        logging.info("MSSQL Database Connected")
    except Exception as e:
        return func.HttpResponse(
            f"Error in sql database connection : {e}", 
            status_code=400
        )
        sys.exit()

    # Query DB for all records without a releaseDate
    cursor.execute("SELECT DISTINCT actionName FROM dbo.Tracking_Actions")
    actionsList = cursor.fetchall()

    tz_est = pytz.timezone('US/Eastern')
    timestamp = datetime.now(pytz.timezone('UTC'))
    timestamp_est = timestamp.astimezone(tz_est)
    timestamp_est_f = timestamp_est.strftime("%m/%d/%Y %I:%M %p")
    
    try:
        cursor.execute("INSERT INTO dbo.Tracking([action],[amount],[timestamp]) values (?,?,?)", action, amount, timestamp)
        sqlConnStr.commit()
    except Exception as e:
        return func.HttpResponse(
            f"Unable to insert new record : {e}", 
            status_code=400
        )
        sys.exit()

    cursor.execute("SELECT amountUnit FROM dbo.Tracking_Actions WHERE actionName = ?", action)
    amount_unit = cursor.fetchone()
    if not amount_unit:
        return func.HttpResponse(
            f"{action} was successfully logged, but no relevant [action] found in DB. Please create new [action] record.",
            status_code=202
        )
    else:
        return func.HttpResponse(
            f"{amount} {amount_unit[0]} of {action} successfully logged at {timestamp_est_f}",
            status_code=200
        )
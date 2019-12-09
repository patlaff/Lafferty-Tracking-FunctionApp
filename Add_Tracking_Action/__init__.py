# Import Modules
from __future__ import print_function
import os
import sys
import json
import pyodbc
import logging
import azure.functions as func
from datetime import datetime

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Azure Function, Lafferty-Tracking, processed a request via HTTP Trigger. This action adds a new action to the DB if not exists.')

    # Parse parameters. Parameters can be passed in either query string or request body
    action = req.params.get('action')
    unit = req.params.get('unit')
    if not action:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            action = req_body.get('action')

    if not unit:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            unit = req_body.get('unit')

    if not action:
        return func.HttpResponse(
            "Please pass an [action] name and [unit] value on the query string or in the request body",
            status_code=400
        )
        sys.exit()
    
    if not unit:
        return func.HttpResponse(
            "Please pass an [action] name and [unit] value on the query string or in the request body",
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

    timestamp = datetime.now()
    if action not in actionsList[0]:
        try:
            cursor.execute("INSERT INTO dbo.Tracking_Actions([actionNAme],[amountUnit],[addedOn]) values (?,?,?)", action, unit, timestamp)
            sqlConnStr.commit()
            return func.HttpResponse(
                f"New Action, {action}, added to Tracking_Actions table with units, {unit}.",
                status_code=200
            )
        except Exception as e:
            return func.HttpResponse(
                f"Unable to insert new record : {e}", 
                status_code=400
            )
            sys.exit()
    else:
        return func.HttpResponse(
            f"{action} already exists in DB."
        )

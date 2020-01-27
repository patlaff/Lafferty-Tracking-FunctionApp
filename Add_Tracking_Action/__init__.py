# Import Modules
from __future__ import print_function
import os
import sys
import json
import logging
import urllib
import sqlalchemy as db
import azure.functions as func
from datetime import datetime

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Azure Function, Lafferty-Tracking, processed a request via HTTP Trigger. This action adds a new action to the DB if not exists.')

    # Parse parameters. Parameters can be passed in either query string or request body
    action = req.params.get('action')
    unit = req.params.get('unit')
    action_type = req.params.get('type')
    timestamp = datetime.now()
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
    
    if not action_type:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            action_type = req_body.get('type')

    if not action:
        return func.HttpResponse(
            "Please pass an [action] name, [unit] value, and action [type] on the query string or in the request body",
            status_code=400
        )
        sys.exit()
    
    if not unit:
        return func.HttpResponse(
            "Please pass an [action] name, [unit] value, and action [type] on the query string or in the request body",
            status_code=400
        )
        sys.exit()
    
    if not action_type:
        return func.HttpResponse(
            "Please pass an [action] name, [unit] value, and action [type] on the query string or in the request body",
            status_code=400
        )
        sys.exit()

    ## Connect to SQL DB
    try:
        params = urllib.parse.quote_plus('DRIVER={ODBC Driver 17 for SQL Server}; SERVER='+os.environ['db_server']+'; DATABASE='+os.environ['db']+'; UID='+os.environ['db_username']+'; PWD='+os.environ['db_password'])
        engine = db.create_engine("mssql+pyodbc:///?odbc_connect=%s" % params)
        connection = engine.connect()
        logging.info("MSSQL Database Connected")
    except Exception as e:
        return func.HttpResponse(
            f"Error in sql database connection : {e}", 
            status_code=400
        )
        sys.exit()

    # Get DB Metadata
    metadata = db.MetaData()

    # Define Tables
    tbl_Tracking_Actions = db.Table('Tracking_Actions', metadata, schema='trk', autoload=True, autoload_with=engine)

    # Query DB for all records without a releaseDate
    try:
        action_query = db.select([tbl_Tracking_Actions.columns.actionName.distinct()])
        actions = connection.execute(action_query).fetchall()
    except Exception as e:
        return func.HttpResponse(
            "Unable to retrieve tracked actions.",
            status_code=400
        )
    actionsList = [r[0] for r in actions]

    if action not in actionsList:
        try:
            insert_query = db.insert(tbl_Tracking_Actions).values(actionName=action, amountUnit=unit, actionType=action_type, addedOn=timestamp)
            insert_result = connection.execute(insert_query)
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

    try:
        connection.close()
    except Exception as e:
        print(f"Error closing db connection: {e}")
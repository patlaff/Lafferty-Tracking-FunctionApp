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
    logging.info('Azure Function, Lafferty-Tracking, processed a request via HTTP Trigger. This action returns the action type of the requested action.')

    # Parse parameters. Parameters can be passed in either query string or request body
    action = req.params.get('action')
    if not action:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            action = req_body.get('action')

    if not action:
        return func.HttpResponse(
            "Please pass an [action] name on the query string or in the request body",
            status_code=400
        )
        sys.exit()

    # Connect to SQL DB
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

    # Get unit for action record
    try:
        type_query = db.select([tbl_Tracking_Actions.columns.actionType]).where(tbl_Tracking_Actions.columns.actionName == action)
        action_type = connection.execute(type_query).scalar()
    except Exception as e:
        return func.HttpResponse(
            "Unable to query DB for action type.",
            status_code=400
        )

    if not action_type:
        return func.HttpResponse(
            f"Action Type for {action} could not be found.",
            status_code=400
        )
    else:
        return func.HttpResponse(
            action_type,
            status_code=200
        )

    try:
        connection.close()
    except Exception as e:
        print(f"Error closing db connection: {e}")
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
    logging.info('Azure Function, Lafferty-Tracking, processed a request via HTTP Trigger. This action returns the list of tracked actions.')

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

    # Query DB for list of Actions
    try:
        action_query = db.select([tbl_Tracking_Actions.columns.actionName])
        actionList = connection.execute(action_query).fetchall()
    except Exception as e:
        return func.HttpResponse(
            f"Error Querying DB: {e}",
            status_code=400
        ) 

    if not actionList:
        return func.HttpResponse(
            f"No actions returned...",
            status_code=404
        )
    else:
        actions = []
        for action in actionList:
            actions.append(action.actionName)
        return func.HttpResponse(
            str(actions), 
            status_code=200
        )
    
    try:
        connection.close()
    except Exception as e:
        print(f"Error closing db connection: {e}")
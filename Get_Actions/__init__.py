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
    logging.info('Azure Function, Lafferty-Tracking, processed a request via HTTP Trigger. This action returns the list of tracked actions.')

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

    # Query DB for list of Actions
    try:
        cursor.execute("SELECT actionName FROM Tracking_Actions")
        actionList = cursor.fetchall()
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

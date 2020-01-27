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
    logging.info('Azure Function, Lafferty-Tracking, processed a request via HTTP Trigger. This action returns the last entry of the requested action.')

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
        sqlConnStr = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server}; SERVER='+os.environ['db_server']+'; DATABASE='+os.environ['db']+'; UID='+os.environ['db_username']+'; PWD='+os.environ['db_password'])
        cursor = sqlConnStr.cursor()
        logging.info("MSSQL Database Connected")
    except Exception as e:
        return func.HttpResponse(
            f"Error in sql database connection : {e}", 
            status_code=400
        )
        sys.exit()

    # Query DB for last Action
    try:
        cursor.execute("""
        SELECT t.action, t.amount, t.[timestamp], a.amountUnit
        FROM trk.Tracking t
        LEFT JOIN trk.Tracking_Actions a
            ON t.action = a.actionName
        WHERE t.action = ?
        AND t.[timestamp] = (SELECT MAX(t.[timestamp]) FROM trk.Tracking t WHERE t.action = ?)
        """, action, action)
        lastAction = cursor.fetchone()
    except Exception as e:
        return func.HttpResponse(
            f"Error Querying DB: {e}",
            status_code=400
        ) 

    if not lastAction:
        return func.HttpResponse(
            f"No instances of the action, {action}, tracked in DB.",
            status_code=404
        )
    else:
        if lastAction.amount % 1 == 0:
            amount = int(lastAction.amount)
        else:
            amount = lastAction.amount
        amountUnit = lastAction.amountUnit
        
        tz_est = pytz.timezone('US/Eastern')
        today_utc = datetime.now(pytz.timezone('UTC'))
        
        timestamp = lastAction.timestamp
        timestamp_utc = pytz.timezone('UTC').localize(timestamp)
        datediff = abs(today_utc - timestamp_utc)
        datediff_hours = int(divmod(abs(today_utc - timestamp_utc).total_seconds(), 3600)[0])
        datediff_hours_rem = datediff_hours - (datediff.days*24)

        timestamp_est = timestamp_utc.astimezone(tz_est)
        timestamp_est_f = timestamp_est.strftime("%m/%d/%Y %I:%M %p")
        
        if datediff.days == 0:
            response = f"{amount} {amountUnit} of {action} was recorded on {timestamp_est_f} EST, {datediff_hours} hours ago."
        else:
            response = f"{amount} {amountUnit} of {action} was recorded on {timestamp_est_f} EST, {datediff.days} days and {datediff_hours_rem} hours ago."
        return func.HttpResponse(
            response,
            status_code=200
        )

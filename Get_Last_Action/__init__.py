# Import Modules
from __future__ import print_function
import os
import sys
import json
import pytz
import logging
import urllib
import sqlalchemy as db
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

    # Define Timezone
    tz_est = pytz.timezone('US/Eastern')
    today_utc = datetime.now(pytz.timezone('UTC'))

    # Connect to SQL DB
    try:
        params = urllib.parse.quote_plus('DRIVER={ODBC Driver 17 for SQL Server}; SERVER='+os.environ['db_server']+'; DATABASE='+os.environ['db']+'; UID='+os.environ['db_username']+'; PWD='+os.environ['db_password'])
        engine = db.create_engine("mssql+pyodbc:///?odbc_connect=%s" % params)
        connection = engine.connect()
        logging.info("MSSQL Database Connected")
    except Exception as e:
        return func.HttpResponse(
            f"Error establishing sql database connection : {e}", 
            status_code=400
        )
        sys.exit()

    # Get DB Metadata
    metadata = db.MetaData()

    # Define Tables
    last_action_vw = db.Table('last_action_vw', metadata, schema='trk', autoload=True, autoload_with=engine)
    
    # Query DB for last Action
    try:
        lastAction_query = db.select([last_action_vw]).where(last_action_vw.columns.action == action)
        lastAction = connection.execute(lastAction_query).fetchone()
        lastAction_unit = db.select([last_action_vw.columns.amountUnit]).where(last_action_vw.columns.action == action)
        amountUnit = connection.execute(lastAction_unit).scalar()
        lastAction_amount = db.select([last_action_vw.columns.amount]).where(last_action_vw.columns.action == action)
        amount = connection.execute(lastAction_amount).scalar()
        lastAction_timestamp = db.select([last_action_vw.columns.max_timestamp]).where(last_action_vw.columns.action == action)
        timestamp = connection.execute(lastAction_timestamp).scalar()
    except Exception as e:
        print(
            "Unable to retrieve unit for action record"
        )

    if not lastAction:
        print(
            f"No instances of the action, {action}, tracked in DB."
        )
    else:
        if amount % 1 == 0:
            amount = int(amount)

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
        print(
            response
        )
        
    try:
        connection.close()
    except Exception as e:
        print(f"Error closing db connection: {e}")

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
from datetime import datetime, timedelta

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Azure Function, Lafferty-Tracking, processed a request via HTTP Trigger.')

    # Parse parameters. Parameters can be passed in either query string or request body
    action = req.params.get('action')
    amount = req.params.get('amount')
    hours_ago = req.params.get('hours_ago')
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

    if not hours_ago:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            hours_ago = req_body.get('hours_ago')

    if not action:
        return func.HttpResponse(
            "Please pass an [action] name, [amount] value, and [hours_ago] value on the query string or in the request body",
            status_code=400
        )
        sys.exit()
    
    if not amount:
        return func.HttpResponse(
            "Please pass an [action] name, [amount] value, and [hours_ago] value on the query string or in the request body",
            status_code=400
        )
        sys.exit()

    if not hours_ago:
        return func.HttpResponse(
            "Please pass an [action] name, [amount] value, and [hours_ago] value on the query string or in the request body",
            status_code=400
        )
        sys.exit()

    # Define Timestamp
    tz_est = pytz.timezone('US/Eastern')
    timestamp_now = datetime.now(pytz.timezone('UTC'))
    timestamp = timestamp_now - timedelta(hours=int(hours_ago))
    timestamp_est = timestamp.astimezone(tz_est)
    timestamp_est_f = timestamp_est.strftime("%m/%d/%Y %I:%M %p")

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
    tbl_Tracking = db.Table('Tracking', metadata, schema='trk', autoload=True, autoload_with=engine)
    tbl_Tracking_Actions = db.Table('Tracking_Actions', metadata, schema='trk', autoload=True, autoload_with=engine)

    # Insert new action record
    try:
        insert_query = db.insert(tbl_Tracking).values(action=action, amount=amount, timestamp=timestamp)
        insert_result = connection.execute(insert_query)
    except Exception as e:
        return func.HttpResponse(
            f"Unable to insert new record : {e}", 
            status_code=400
        )
        sys.exit()

    # Get unit for action record
    try:
        unit_query = db.select([tbl_Tracking_Actions.columns.amountUnit]).where(tbl_Tracking_Actions.columns.actionName == action)
        amount_unit = connection.execute(unit_query).scalar()
    except Exception as e:
        return func.HttpResponse(
            "Unable to retrieve unit for action record",
            status_code=400
        )

    if not amount_unit:
        return func.HttpResponse(
            f"{action} was successfully logged, but no relevant [action] found in DB. Please create new [action] record.",
            status_code=202
        )
    else:
        return func.HttpResponse(
            f"{amount} {amount_unit} of {action} successfully logged at {timestamp_est_f}",
            status_code=200
        )

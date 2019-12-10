# Personal Tracking Application

This app was written to provide a personal tracking framework using the following tools:

- Python
- Azure Functions
- Azure SQL DB
- Power BI
- Siri Shortcuts

Siri Shortcuts acts as the front end for easily interfacing with the Database by calling API endpoints surfaced by the Azure Function written in Python.  Power BI is then used to set up data alerts to notify the user if any action is past a certain threshold.

## SQL DB Tables

The framework makes use of just two tables, dbo.Tracking, which tracks facts, and a dimension table, dbo.Tracking_Actions, which lists all tracked actions and details about them including the type of units used to quantify each entry

- dbo.Tracking
    - action        string      FK
    - amount        number
    - timestamp     datetime
    - location      string

- dbo.Tracking_Actions
    - actionName    string      PK
    - amountUnit    number
    - addedOn       datetime

## Azure Functions

### Get_Actions

**Arguments**

This function takes no arguments

This function returns a distinct list of **ActionName** from dbo.Tracking_Actions


### Get_Last_Action

**Arguments**
- Action        string

This function returns the most recent value for any given **Action** in dbo.Tracking


### Add_Tracking_Action

**Arguments**
- Action        string
- Unit          string

This function inserts new records to the dbo.Tracking_Actions table.


### Lafferty_Tracking

**Arguments**
- Action        string
- Unit          number
- Location      string  (optional)

This function inserts new records to the dbo.Tracking table.
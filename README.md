# Fleetmetrica Python challenge

Submission for a Fleetmetrica Inc's Python challenge by Rotola Akinsowon.

## Contents

* [Requirements & Setup](#Requirements-&-Setup)
* [Configuration](#configuration)
* [Running The App](#running-the-app)
* [Task Description](#task-description)

## Requirements & Setup

Listed below are the core requirements of the application

- [Python 3.8](https://www.python.org/downloads/release/python-380/) or higher
- [PIP 3](https://pip.pypa.io/en/stable/installation/) - Typically present with your python installation, if not you
  can install following the guide
- [Nodejs](https://nodejs.org/en/) 14.18 or higher
- [Docker](https://docs.docker.com/get-docker/)

### Setup
This app was built and tested on Ubuntu Linux, but the scripts should be compartible with most unix based systems.
A one-time setup is required in other to run the app properly, this is done by running the following command
  ```shell
  # from the apps root dir in a bash shell
  ./run init
  ```
The setup initializes the python environment and the serverless credentials

## Configuration

The CLI configuration is managed using a local environments file located at *./envs/local.env*. The following 
environment variable 
that can be set for the CLI 
utility


| Name | Description                              | Required    | conditions                                     |
|------|------------------------------------------|-------------|------------------------------------------------|
|  PGDATABASE   | Name of the database to save logs to     | true        |                                                |
|  PGUSER   | Postgres database username               | conditional | required is the database requires it           |
|  PGHOST        | Database host                            | false       |                                                |
|  PGPORT          | Postgres database port, defaults to 5432 | false       |                                                |
|  S3_BUCKET_NAME  | AWS s3 bucket to save generated files to | conditional | required when running as a serverless function |
|  AWS_ACCESS_KEY  | Access key ID for AWS                    | conditional | required when running as a serverless function |
|  AWS_SECRET_KEY  | secret key ID for AWS                    |  conditional           |  required when running as a serverless function                                              |

## Running The App

The CLI accepts the following parameters:

- `date_range`[optional]: a date range for which you want to generate mock data for with the format mm-dd-yy:mm-dd-yy 
  e.g 10-13-22:10-16-22. If not specified it defaults to 7 days and accepts a max of 30 days
- `data_size`[optional]: Number of records to generate in the mock data, done with a best effort approach. Defaults to 
  2000
- `config`[required]: data source configuration, a predefined config to process the file with, currently there are 
  configurations for generating performance and daily reports.
- `store`[optional]: object storage location, location to store generated mock data in. When running as a serverless 
  function this will be an s3 bucket path. Defaults to *./mocks*

The CLI can be run both on a local machine or as a serverless function. See examples below for running it using both 
methods

**Local Machine**
```shell
# generate perfomance mocks with size and date range arguments
python fleetmocker.py --files ./cli/fixtures/PERFORM_20200911.csv --config performance --data_size 30000 --date_range 10-13-22:10-16-22
```
<br/>

**Serverless Function**

First we must deploy the serverless function to AWS
```shell
sls deploy --stage dev
```

After deployment, we can invoke it with
```shell
# we can pass in any acceptable combination of param in the data string
sls invoke -f fleetmocker --data '--files ./cli/fixtures/PERFORM_20200911.csv --config performance'
```

<br><br>


## Task Description

Fleetmetrica needs a CLI utility written in Python to generate mock vehicle test data based on a sample
data file. The mock data set needs to scale across multiple vehicle, drivers, and date ranges and be able
to generate realistic fleet level data set from a single daily sample. The CLI utility should be data agnostic, able 
to process different CSV files regardless of the format based on a configuration file. Data should
be generated based on randomized pattern generation to allow using the mock data set in end-to end
testing using our statistical analysis engine. A final report should be generated in HTML.

Inputs
Sample data files
There are 2 different sample data set provided:
- Dataset #1 contains 1 file PERFORM_20200911.CSV
- Dataset #2 contains 2 files: SG_20200609_DAILY_DRIVER_INCIDENT.CSV and
SG_20200609_DAILY_DRIVER_SUMMARY.CSV

Processing Parameters
- Date range for the mock dataset
- Data size for the mock dataset
- Object Storage location to store the generated mock dataset.
- Data Source Configuration
- Pattern Options

Output files
- Mock dataset files in object storage
- HTML report in object storage

Logs
- All processing logs and metrics should be stored in a PostgreSQL database

Technical Requirements &amp; Notes
- Manageability, Portability, and code quality are more important than using the latest &amp;
greatest features.
- Completeness and documentation are more important than extra features.
- Follow as much as possible the The Twelve-Factor App (12factor.net) philosophy.
- CLI should be able to run as a serverless function on AWS lambda.

Deliverables
The final product of the technical challenge should be submitted in a GitHub repository. The repository
should include the following:
- Full commit history (to show progress through the challenge)
- All source code
- Sample configuration files
- Setup and build scripts
- Documentation.
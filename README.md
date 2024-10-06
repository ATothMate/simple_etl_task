# sdu_qm_task

An exemplary repository to contain a simple ETL solution.

## Background

The fundamental business case behind this solution is about an Ireland-based
 transaction processing center.  
This center accepts transactions from all over the world. The current state of
 their processing generates data in the following fashion:  

|UserId|TransactionId|TransactionTime|ItemCode|ItemDescription|NumberOfItemsPurchased|CostPerItem|Country|
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
|325794|6365337|Tue Feb 05 13:10:00 IST 2019|472731|RETROSPOT BABUSHKA DOORSTOP|6|5.18|United Kingdom|
|...|...|...|...|...|...|...|...|
|259770|6008596|Tue May 22 08:48:00 IST 2018|478464|LANTERN CREAM GAZEBO |18|6.84|Cyprus|

They wish to warehouse all incoming transaction snapshots, and wish to seek
 advisory on how they may enhance their transaction recording processes.

During the initial discussions, certain concerns were mentioned:
- the transaction recording process had a bug, during a certain period, which
  might affect certain transaction timestamps. Specifically, the currently
  used timezones are IST (Ireland Standard Time), UTC, and GMT. Any timestamp
   containing other timezones should be somehow flagged for evalution.
- due to another bug, certain transactions might have been recorded multiple
  times, filtering these entries are particularly important.

## Solution

The current state of the service is able to:
- filter any duplicate entries, preventing those from entering the
  business-critical layer.
- flag, isolate, and archive any entries with unfit transaction time.

### Addition

During the development process certain pain-points surfaced, which might take a
 toll on the overall business and decision-making:
- generally, it seems that transaction times are not granular enough to enable
  finer insight into the data and later the business. Improving the recording
  process would greatly benefit both the warehousing and any data-driven
  decision-making later.
- also, it seems that certain item codes are the same for products with
  different item description. Should this issue be handled, it would also
  support the above mentioned causes.

## Prerequisites

### Prerequisites for the demonstration

- **Docker Desktop**: to run the containerized application.
- **.env** file: a file containing the required PSQL environmental variables for
  the `docker-compose.yml` and the services. The `.env` file should have the
  content of:
    ``` shell
    POSTGRES_USER=_user_  
    POSTGRES_PASSWORD=_password_  
    POSTGRES_DB=_dbname_  
    POSTGRES_HOST=postgres_db  # name of the PSQL service, defined in the docker-compose.yml
    POSTGRES_PORT=5432  # exposed port of the PSQL service, defined in the docker-compose.yml
    ```
   The file should be placed in the folder: `./docker/`.

- **Git Bash**: to remove any trailing `\r` characters from the required
  `./docker/.env` file:
 ``` shell
 cd /path/to/repository/base/folder
 sed -i 's/\r$//' ./docker/.env
 ```

 - (*Optional*) Database administration tool, such as
   [pgAdmin](https://www.pgadmin.org/) or [DBeaver](https://dbeaver.io/): to
   inspect the results of the demonstration.

###  Prerequisites for local experimenting and development

- Required Python packages are listed in the `requirements.txt` file (for
  `Python 3.12`).

## Running the POC solution

The underlying POC solution builds on 3 services:
- a **PostgreSQL database**: responsible for warehousing the transaction
  records.
- an **Initializer**: responsible for the initialization of the relational
  tables.
- a simple **ETL pipeline**: responsible for transporting the transaction
  snapshots into the destination database.

To initiate the demonstrative process, run the following command from the base
 folder:
``` shell
docker compose -f .\docker\docker-compose.yml up
```

Upon executing the command, the defined images will be created and the services
 will start their processes.

### Step-by-Step

Upon executing the command, the images and the containers will be created.

The main service, on which the other to are dependant, is the `postgres_db`.
 After creation a regular health check is run on this service. The service
 will remain active.

The next service is the `database_init`, which waits until the `postgres_db`
 service becomes healthy. After that, it initiates the required relational
 tables. The service will stop after successful table creation.

Finally, the `etl_service` starts its processes. This service contains 3
 sub-services/modules which are run periodically as a cron job. The cycle is:
- a *feeder* sub-service looks for any available transaction snapshot source
  files. If found, it replaces 1 to enable the next service's
  processes.  
  - Source folder during the demonstration: `data_folder_source`.  
  - Destination folder during the demonstration: `data_folder_monitor`.  

- a *pre_loader* sub-service monitors the destination folder of the *feeder* to
  initiate an ETL process on all available source files. This sub-service is 
  responsible for loading data from source files into a PostgreSQL database. It
  follows the Extract-Transform-Load (ETL) pattern; extracting data from newly
  available source files, transforming the data as needed, and loading it into
  the *preload table*.  
  The service also creates archives of unvonvertible transaction records, to
  highlight timestamp related issues and enable further decission-making.  
  - Source folder during the demonstration: `data_folder_monitor`.  
  - Archive folder during the demonstration: `data_folder_archive`.  

- a *delta_loader* sub-service queries the content of the *preload table*, to
  detect any new entries for warehousing, enabling business processes to analyze
  the transaction data in the desired fashion.

With the current demonstration the process takes 3 cycles to process all source
 files (due to the 3 starting *CSV* files). After that the log messages should
 contain information:
 - by the ***feeder***:  
   Looking for available source file in: /app/data_folder_source.  
   Found no processable file.
 - by the ***pre_loader***:  
   Found 0 new source CSV files compared to the DB.  
   No data to insert to 'preload_transaction'.
 - by the ***delta_loader***:  
   Found 0 new entries in 'preload_transaction' table.  
   Skipping insertion as there is no new entry.

After these messages, **the demonstration can be stopped**, by hitting: `Ctrl+c`

#### Inspection

To inspect the results of the demonstration, connect to the initiated PostgreSQL
 database on an administration tool.  
Connection is possible by entering the parameters stored in the `.env` file
 (except for the host and port), such as:
 |parameter|value|
 |:-:|:-:|
 |user|_user in `.env` file_|
 |password|_password in `.env` file_|
 |database (db) |_db in `.env` file_|
 |host|**localhost**|
 |port|5431|

##### Example queries for inspection

- **Pre-load table**: `preload_transaction`
``` SQL
SELECT * FROM preload_transaction; -- select all entries from the preload table.

-- to find duplicate hash_id entries in the preload_transaction table
SELECT hash_id, COUNT(*) as duplicate_count
FROM preload_transaction
GROUP BY hash_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;
```

- **Delta-load tables**: `dim_location`, `dim_item`, `dim_date`,
  `fact_transaction`
``` sql
SELECT * FROM dim_location; -- select all entries from the location dimension table.
```

``` sql
SELECT * FROM dim_item; -- select all entries from the item dimension table.
```

``` sql
SELECT * FROM dim_date; -- select all entries from the date dimension table.
```

``` sql
SELECT * FROM fact_transaction; -- select all entries from the transaction fact table.

-- find the:
--   total transaction on each continent, 
--   total revenue generated by each continent,
--   the most frequently purchased item for each location.
SELECT 
    dl.continent AS continent,
    COUNT(transaction_id) AS total_transactions,
    SUM(total_cost) AS total_revenue,
    MAX(di.description) AS most_frequent_item,
    COUNT(item_id) AS item_count
FROM fact_transaction AS ft
LEFT JOIN dim_location AS dl
	ON ft.location_id = dl.id
LEFT JOIN dim_item AS di
	ON  ft.item_id = di.id
GROUP BY dl.continent
ORDER BY total_revenue DESC;
```


## Testing

### Automatically

Tests are automatically run after every push to the `main` branch, and after
 any Pull Request created for the `main` branch.

### Manually

To test any change against the developed unit tests, run the following command
 from the base folder:
``` shell
python -m pytest tests
```

To test adherence to the defined linting, run the following command(s)
 from the base folder:

``` shell
python -m flake8 sdu_qm_task
python -m flake8 tests
```

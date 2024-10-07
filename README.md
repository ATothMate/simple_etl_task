# sdu_qm_task

Repository to contain a simple ETL solution.

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

They wish to warehouse all incoming transaction snapshots and seek
 advisory on how they may enhance their transaction recording processes.

During the initial discussions, certain concerns were mentioned:
- the transaction recording process had a bug, during a certain period, which
  might affect certain transaction timestamps. Specifically, the currently
  used timezones are IST (Ireland Standard Time), UTC, and GMT. Any timestamp
   containing other time zones should be somehow flagged for evaluation.
- due to another bug, certain transactions might have been recorded multiple
  times, filtering these entries is particularly important.

## Solution

The current state of the service is able to:
- filter any duplicate entries, preventing those from entering the
  business-critical layer.
- flag, isolate, and archive any entries with unfit transaction time.

### Addition

During the development process, certain pain points surfaced, which might take a
 the toll on the overall business and decision-making:
- generally, it seems that transaction times are not granular enough to enable
  finer insight into the data and later the business. Improving the recording
  process would greatly benefit both the warehousing and any data-driven
  decision-making later.
- also, it seems that certain item codes are the same for products with
  different item description. Should this issue be handled, it would also
  support the above-mentioned causes.
- it was also quite interesting to see, how certain countries were recorded
  as it can be observed with the final query on the fact_transaction table, 
  the second largest revenue comes from the continent "UNKOWN", which is a
  result of unconventional country names and notations. The decision was made to
  include these in the form of "UNKNOWN"s to raise awareness, and to hasten
  any decision regarding.

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
 will start their processes. The whole demonstration takes approximately
 3-4 minutes and is orchestrated by the cron job which initiates and imitates
 a real-world nightly batch processing.

### Step-by-Step

Upon executing the command, the images and the containers will be created.

The main service, on which the other to are dependent, is the `postgres_db`.
 After creation, a regular health check is run on this service. The service
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
  The service also creates archives of unconvertible transaction records, to
  highlight timestamp-related issues and enable further decision-making.  
  - Source folder during the demonstration: `data_folder_monitor`.  
  - Archive folder during the demonstration: `data_folder_archive`.  

- a *delta_loader* sub-service queries the content of the *preload table*, to
  detect any new entries for warehousing, enabling business processes to analyze
  the transaction data in the desired fashion.

At the very beginning new folders will be created in the base folder of the
 repository, to initiate the 3 data container folders:
- `data_folder_source` - the source folder of the *feeder* sub-service. It is
  being monitored periodically, and if there is an available source file, it
  will be moved to the input folder of the *pre-loader* sub-service.
- `data_folder_monitor`: the input folder for the *pre_loader* sub-service. The
  service periodically checks the content and creates any delta load compared to
  the currently available in the DB.
- `data_folder_archive`: this folder is responsible for storing any
  unconvertible set of entries after each *pre_loader* cycle. These archived
  sets can be evaluated later.

With the current demonstration, the process takes 3 cycles to process all source
 files (due to the 3 starting *CSV* files). After that, the log messages should
 contain information:
 - by the ***feeder***:  
   Looking for available source files in: /app/data_folder_source.  
   Found no processable file.
 - by the ***pre_loader***:  
   Found 0 new source CSV files compared to the DB.  
   No data to insert to 'preload_transaction'.
 - by the ***delta_loader***:  
   Found 0 new entries in the 'preload_transaction' table.  
   Skipping insertion as there is no new entry.

After these messages, **the demonstration can be stopped**, by hitting: `Ctrl+c`

### Results of the demonstration

Ultimately (after 3 cycles) the **data folders** should contain:

- `data_folder_source` - empty as the *feeder* sub-service moved all the source
  files to the `data_folder_monitor`.
- `data_folder_monitor` - 3 files, which were moved be the
  *feeder* process and processed by the *pre_loader* processes.
- `data_folder_archive` - 2 archived files (1 from `transactions_1_100k.csv` and
  1 from `transactions_2_100k.csv`), which store the entries (3 from the former,
  3 from the latter source file) that were not fit for the transformation during
  the *pre_loader* ETL process.  
The 6 entries in the archived folder have truly unexpected time zones in their
 timestamp attributes, confirming the filtering feature of the *pre_loader*
   - Mon Jul 02 07:33:00 `XST` 2018
   - Sat Feb 24 12:46:00 `JST` 2018
   - Sun Feb 25 11:56:00 `ABC` 2018
   - Tue Oct 02 08:04:00 `YYZ` 2018
   - Wed May 30 08:04:00 `TXT` 2018
   - Mon Dec 24 12:40:00 `3ZP` 2018


The **tables in the database** should contain:

- `preload_transaction` - 299_994 entries (3*100_000 - 6 unconvertible).
- `dim_location` - 34 entries (33 valid location entries and 1 UNKNOWN).
- `dim_item` - 3_314 entries.
- `dim_date` - 305 entries.
- `fact_trnsaction` - 257_244 deduplicated entries.

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

-- resulting in 42_272 rows.
-- with 'ac8958e78f07303407551793831b0407' present 10 times in the table.

-- to inspect the infamous transaction
select * from preload_transaction
where hash_id = '9d89c851ae57c09887225b20041c0bb6'
-- results are shown in the table below
```
|id|hash_id|source_file|transaction_id|user_id|transaction_time|item_code|item_description|item_quantity|cost_per_item|country|created_at|
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
|32114|ac8958e78f07303407551793831b0407|transactions_1_100k.csv|6110764|355383|2018-08-17 07:37:00|476658|PINK REGENCY TEACUP AND SAUCER|3|4.08|United Kingdom|2024-10-07 09:03:02.941009|
|36393|ac8958e78f07303407551793831b0407|transactions_1_100k.csv|6110764|355383|2018-08-17 07:37:00|476658|PINK REGENCY TEACUP AND SAUCER|3|4.08|United Kingdom|2024-10-07 09:03:02.941009|
|203869|ac8958e78f07303407551793831b0407|transactions_3_100k.csv|6110764|355383|2018-08-17 07:37:00|476658|PINK REGENCY TEACUP AND SAUCER|3|4.08|United Kingdom|2024-10-07 09:05:02.65903|
|227454|ac8958e78f07303407551793831b0407|transactions_3_100k.csv|6110764|355383|2018-08-17 07:37:00|476658|PINK REGENCY TEACUP AND SAUCER|3|4.08|United Kingdom|2024-10-07 09:05:02.65903|
|126393|ac8958e78f07303407551793831b0407|transactions_2_100k.csv|6110764|355383|2018-08-17 07:37:00|476658|PINK REGENCY TEACUP AND SAUCER|3|4.08|United Kingdom|2024-10-07 09:04:01.891237|
|201241|ac8958e78f07303407551793831b0407|transactions_3_100k.csv|6110764|355383|2018-08-17 07:37:00|476658|PINK REGENCY TEACUP AND SAUCER|3|4.08|United Kingdom|2024-10-07 09:05:02.65903|
|272552|ac8958e78f07303407551793831b0407|transactions_3_100k.csv|6110764|355383|2018-08-17 07:37:00|476658|PINK REGENCY TEACUP AND SAUCER|3|4.08|United Kingdom|2024-10-07 09:05:02.65903|
|26419|ac8958e78f07303407551793831b0407|transactions_1_100k.csv|6110764|355383|2018-08-17 07:37:00|476658|PINK REGENCY TEACUP AND SAUCER|3|4.08|United Kingdom|2024-10-07 09:03:02.941009|
|124898|ac8958e78f07303407551793831b0407|transactions_2_100k.csv|6110764|355383|2018-08-17 07:37:00|476658|PINK REGENCY TEACUP AND SAUCER|3|4.08|United Kingdom|2024-10-07 09:04:01.891237|
|275305|ac8958e78f07303407551793831b0407|transactions_3_100k.csv|6110764|355383|2018-08-17 07:37:00|476658|PINK REGENCY TEACUP AND SAUCER|3|4.08|United Kingdom|2024-10-07 09:05:02.65903|


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
-- results are shown in the table below
```

|continent|total_transactions|total_revenue|most_frequent_item|item_count|
|:-:|:-:|:-:|:-:|:-:|
|Europe|250_975|18_045_122.28|ZINC WIRE SWEETHEART LETTER TRAY|250_975|
|UNKNOWN|4_459|550_764.42|ZINC WIRE KITCHEN ORGANISER|4_459|
|Oceania|643|281_928.48|YELLOW GIANT GARDEN THERMOMETER|643|
|Asia|924|163_133.52|ZINC METAL HEART DECORATION|924|
|North America|233|10_400.82|YELLOW COAT RACK PARIS FASHION|233|
|South America|10|2_209.02|SET OF 6 SPICE TINS PANTRY DESIGN|10|


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

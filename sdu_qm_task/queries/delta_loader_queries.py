from sdu_qm_task.queries.table_names import *

UNIQUE_DELTA_PRELOAD_TABLE = "unique_delta_preload"

DELTA_QUERY = f"""
WITH fact_sub AS (
    SELECT MAX(created_at) AS max_created_date
    FROM {FACT_TRANSLATION_TABLE}
), {UNIQUE_DELTA_PRELOAD_TABLE} AS (
    SELECT *
    FROM (
		SELECT
			*,
			ROW_NUMBER() OVER(PARTITION BY hash_id ORDER BY created_at) AS row_num
		FROM {PRELOAD_TRANSACTION_TABLE}
	)
    WHERE
		row_num = 1
		AND CASE
	        WHEN (SELECT max_created_date FROM fact_sub) IS NULL THEN TRUE
	        ELSE (SELECT max_created_date FROM fact_sub) < created_at
	    END
)"""

COUNT_DELTA_QUERY = f"""
{DELTA_QUERY}
SELECT COUNT(*)
FROM {UNIQUE_DELTA_PRELOAD_TABLE}
"""

LOCATION_QUERY = f"""
{DELTA_QUERY}
SELECT DISTINCT country
FROM {UNIQUE_DELTA_PRELOAD_TABLE}
WHERE country NOT IN (
    SELECT DISTINCT(country_name)
    FROM {DIM_LOCATION_TABLE}
)
"""

LOCATION_INSERT_CMD = f"""
INSERT INTO {DIM_LOCATION_TABLE}({{columns}})
SELECT '{{values}}'
WHERE NOT EXISTS(
    SELECT country_name
    FROM {DIM_LOCATION_TABLE}
    WHERE country_name = '{{country_name}}'
);
"""

ITEM_INSERT_CMD = f"""
{DELTA_QUERY}
INSERT INTO {DIM_ITEM_TABLE}(id, description)
SELECT
    item_code,
    COALESCE(item_description, 'unknown')
FROM {UNIQUE_DELTA_PRELOAD_TABLE}
ON CONFLICT (id) DO NOTHING
"""

DATE_INSERT_CMD = f"""
{DELTA_QUERY}, pre_transaction_date AS (
    SELECT
        CAST(
            CONCAT(
                EXTRACT(YEAR FROM transaction_time),
                LPAD(EXTRACT(MONTH FROM transaction_time)::TEXT, 2, '0'),
                LPAD(EXTRACT(DAY FROM transaction_time)::TEXT, 2, '0')
            ) AS INTEGER
        ) AS id,
        CAST(transaction_time AS DATE) AS date,
        EXTRACT(YEAR FROM transaction_time) AS year,
        CONCAT('Q', EXTRACT(QUARTER FROM transaction_time)) AS quarter,
        EXTRACT(MONTH FROM transaction_time) AS month,
        EXTRACT(DAY FROM transaction_time) AS day
    FROM {UNIQUE_DELTA_PRELOAD_TABLE}
)
INSERT INTO {DIM_DATE_TABLE}(id, date, year, quarter, month, day)
SELECT id, date, year, quarter, month, day
FROM pre_transaction_date
ON CONFLICT (id) DO NOTHING
"""

FACT_INSERT_CMD = f"""
{DELTA_QUERY}
INSERT INTO {FACT_TRANSLATION_TABLE}
SELECT 
    hash_id,
    transaction_id,
    user_id,
    dd.id AS date_id,
    transaction_time,
    di.id AS item_id,
    item_quantity,
    cost_per_item,
    (item_quantity * cost_per_item) AS total_cost,
    CASE
        WHEN dl.id IS NOT NULL THEN dl.id
        ELSE (SELECT id FROM {DIM_LOCATION_TABLE} WHERE country_name = 'UNKNOWN') END
    AS location_id,
    created_at
FROM {UNIQUE_DELTA_PRELOAD_TABLE} AS pt
LEFT JOIN {DIM_DATE_TABLE} AS dd ON CAST(pt.transaction_time AS DATE) = dd.date
LEFT JOIN {DIM_ITEM_TABLE} AS di ON pt.item_code = di.id
LEFT JOIN {DIM_LOCATION_TABLE} AS dl ON pt.country = dl.country_name;
"""

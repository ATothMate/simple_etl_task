from sdu_qm_task.queries.table_names import (
    PRELOAD_TRANSACTION_TABLE,
    DIM_DATE_TABLE,
    DIM_ITEM_TABLE,
    DIM_LOCATION_TABLE,
    FACT_TRANSLATION_TABLE
)

CREATE_PRELOAD_TRANSACTION = f"""
CREATE TABLE IF NOT EXISTS {PRELOAD_TRANSACTION_TABLE} (
    id INTEGER GENERATED ALWAYS AS IDENTITY,
    hash_id CHAR(32) NOT NULL,
    source_file VARCHAR(100) NOT NULL,
    transaction_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    transaction_time TIMESTAMP NOT NULL,
    item_code INTEGER NOT NULL,
    item_description VARCHAR(255),
    item_quantity INTEGER NOT NULL,
    cost_per_item DECIMAL NOT NULL,
    country VARCHAR(100),
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);
"""

CREATE_DIM_DATE = f"""
CREATE TABLE IF NOT EXISTS {DIM_DATE_TABLE} (
    id INTEGER,
    date DATE NOT NULL,
    year INTEGER NOT NULL,
    quarter CHAR(2) NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    PRIMARY KEY (id)
);
"""

CREATE_DIM_ITEM = f"""
CREATE TABLE IF NOT EXISTS {DIM_ITEM_TABLE} (
    id INTEGER NOT NULL,
    description VARCHAR(255) NOT NULL,
    PRIMARY KEY (id)
);
"""

CREATE_DIM_LOCATION = f"""
CREATE TABLE IF NOT EXISTS {DIM_LOCATION_TABLE} (
    id INTEGER GENERATED ALWAYS AS IDENTITY,
    country_code CHAR(3) NOT NULL,
    country_name VARCHAR(100) NOT NULL,
    continent VARCHAR(20) NOT NULL,
    PRIMARY KEY (id)
);
"""

CREATE_FACT_TRANSCTION = f"""
CREATE TABLE IF NOT EXISTS {FACT_TRANSLATION_TABLE} (
    hash_id CHAR(32) NOT NULL,
    transaction_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    date_id INTEGER NOT NULL,
    transaction_time TIMESTAMP NOT NULL,
    item_id INTEGER NOT NULL,
    item_quantity INTEGER NOT NULL,
    cost_per_item DECIMAL NOT NULL,
    total_cost DECIMAL NOT NULL,
    location_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (hash_id),
    CONSTRAINT fk_date
        FOREIGN KEY (date_id)
            REFERENCES {DIM_DATE_TABLE}(id),
    CONSTRAINT fk_item
        FOREIGN KEY (item_id)
            REFERENCES {DIM_ITEM_TABLE}(id),
    CONSTRAINT fk_location
        FOREIGN KEY (location_id)
            REFERENCES {DIM_LOCATION_TABLE}(id)
);
"""

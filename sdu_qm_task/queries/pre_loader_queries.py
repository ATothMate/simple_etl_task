from sdu_qm_task.queries.table_names import *

PRELOAD_SOURCE_FILE_QUERY = f"""
    SELECT DISTINCT source_file
    FROM {PRELOAD_TRANSACTION_TABLE};
"""

import duckdb
import requests
import glob
import os
import gc
import shutil
import time
from pathlib import Path
import pandas as pd
import os
import dotenv
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from google import genai


dotenv.load_dotenv()

# Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
# Date Transformation
# --- 1. Define the Pydantic Schema for the Transformation Rule ---
class DateParsingRule(BaseModel):
    columns_used: List[str] = Field(
        ..., 
        description="The exact list of column names needed to construct the date."
    )
    join_separator: str = Field(
        " ", 
        description="The separator to use if joining multiple columns (default to space ' '). If single column, this is ignored."
    )
    source_strptime_format: str = Field(
        ..., 
        description="The Python strptime format string matching the source data (e.g., '%Y-%m-%d' or '%B %d, %Y'). If multiple columns, this format must match the joined string."
    )
example_rows = upload_df.head(10).to_markdown()
columns_available = list(upload_df.columns)
target_format_description = historic_df["issue_date"][0]  # Assume we want to match the first date column
print("\nExample Rows from Upload Data:\n", example_rows)
print("\nAvailable Columns:", columns_available)
print("\nTarget Date Format Example:", target_format_description)
# --- 3. Generate the Transformation Rule ---
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=f"You are a Python Data Engineer. I have a dataset with the following columns: {columns_available}\nHere are the first few rows: {example_rows}\nI need to transform the data into this format: {target_format_description}.\nIdentify the columns that contain date information and define a parsing rule.\nIf the date is split across multiple columns, specify the order they should be joined and the format string to parse the result.",
    config={
        "response_mime_type": "application/json",
        "response_json_schema": DateParsingRule.model_json_schema(),
    },
)

rule = DateParsingRule.model_validate_json(response.text)

print(f"LLM Logic Identified:")
print(f"Columns: {rule.columns_used}")
print(f"Format: '{rule.source_strptime_format}'")


# --- 4. APPLY the Transformation (The "ETL" part) ---
# This function uses the LLM's output to actually process the data
def transform_row(row, rule: DateParsingRule):
    try:
        # 1. Extract values based on the columns the LLM identified
        values = [str(row[col]) for col in rule.columns_used]
        
        # 2. Join them (e.g. "2023 October 25")
        raw_date_string = rule.join_separator.join(values)
        
        # 3. Parse using the LLM's format string
        dt_object = datetime.strptime(raw_date_string, rule.source_strptime_format)
        
        # 4. Return in the target format (ISO 8601)
        return dt_object.strftime("%Y-%m-%d")
    except Exception as e:
        return None

# Test on the data
print("\n--- Transformed Data ---")
for row in upload_df.head(10).to_dict(orient="records"):
    new_date = transform_row(row, rule)
    print(f"Original: {row} -> Transformed Date: {new_date}")
# Column Mapping
# --- 1. Define the Pydantic Schema ---
class ColumnPair(BaseModel):
    historical_column: str = Field(
        description="The exact column name from the historical data."
    )
    new_upload_column: Optional[str] = Field(
        description="The matching column name from the new upload. None if no match found."
    )

class MappingResult(BaseModel):
    mappings: List[ColumnPair] = Field(
        description="A list of mappings covering every column in the historical dataset."
    )
prompt = f"""
    You are a data engineering assistant. You are tasked with mapping the output from a new file to historical data. 
    Below are the first 10 rows of the historical data, and the first 10 rows of the new uploaded data. 
    Based on these rows print a dictionary where the key is the column name from the historical data, 
    and the values are the column names from new upload. Each column from the historical data should appear in the dictionary. 
    If a column from the historical data does not have a match then its value should be None. 
    Every column from the new uploaded data does not need a to appear in the final dictionary. 
    If a column from the new upload does not have a match in the historical data, it should not appear in the final dictionary. 
    Only print the dictionary as the final output. 
"""

requirments = """"
    Requirements:
    1. Return a list of mappings.
    2. Every column from the 'Historical Columns' list MUST appear in the output.
    3. If a historical column has no match in the new file, the value must be None.
"""
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# --- 3. Generate Content ---
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=f"{prompt}\n Example of historical columns:\n {historic_df.head(10).to_string()}\n Example of upload columns:\n {upload_df.head(10).to_string()}\n {requirments}",
    config={
        "response_mime_type": "application/json",
        "response_json_schema": MappingResult.model_json_schema(),
    },
)
response.text


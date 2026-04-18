import os

import pandas as pd
from loguru import logger
from pymongo import MongoClient
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from api_fetch import (
    get_cached_quote_data,
    get_cached_income_statement_data,
    compute_fields_not_in_api,
    combine_data_into_dataframe
)

load_dotenv()
api_url_root = os.getenv("API_URL_ROOT")
api_key = os.getenv("API_KEY")

def initiate_mongo_client():
    client = MongoClient("mongodb://mongodb:27017")
    db = client["mini_terminal"]
    collection = db["query_collection_log"]
    return collection

def log_query_in_mongo(
        app_name,
        symbol,
        quote_api_success,
        income_api_success,
        quote_cache_flag,
        income_statement_cache_flag,
):
        collection.insert_one({
            "app_name":app_name,
            "symbol":symbol,
            "request_datetime":pd.Timestamp.now(tz = 'America/Los_Angeles'),
            "quote_api_success":quote_api_success,
            "income_api_success":income_api_success,
            "quote_cache_flag":quote_cache_flag,
            "income_statement_cache_flag":income_statement_cache_flag,
        })

collection = initiate_mongo_client()

try:
    collection.database.client.admin.command("ping")
    logger.info("MongoDB connection successful")
except Exception as e:
    logger.exception(f"MongoDB connection failed: {e}")

if not api_url_root:
    raise ValueError("API URL root note found in .env")
if not api_key:
    raise ValueError("API key not found in .env")


app = FastAPI()
class QueryRequest(BaseModel):
    symbol:str
    app_name:str

class QueryResponse(BaseModel):
    rows:list
    quote_data:dict
    income_statement_data:dict
    quote_cache_flag:bool
    income_statement_cache_flag:bool

@app.post("/query")
def run_query(request:QueryRequest):

    symbol = request.symbol.strip().upper()

    if len(symbol) > 5:
        raise HTTPException(status_code=422,detail="ticker symbol cannot be more than 5 characters")

    quote_data,quote_cache_flag = get_cached_quote_data(
        symbol,
        api_url_root,
        api_key
    )

    income_statement_data,income_statement_cache_flag = get_cached_income_statement_data(
        symbol,
        api_url_root,
        api_key
    )

    other_data = compute_fields_not_in_api(quote_data,income_statement_data)

    combined_df = combine_data_into_dataframe(
        quote_data,
        income_statement_data,
        other_data
    )

    quote_api_success = False
    income_api_success = False
    if quote_data != {}:
        quote_api_success = True
    if income_statement_data != {}:
        income_api_success = True

    log_query_in_mongo(
        request.app_name,
        symbol,
        quote_api_success,
        income_api_success,
        quote_cache_flag,
        income_statement_cache_flag
    )
    
    return QueryResponse(
        rows = combined_df.to_dict(orient="records"),
        quote_data = quote_data,
        income_statement_data = income_statement_data,
        quote_cache_flag = quote_cache_flag,
        income_statement_cache_flag = income_statement_cache_flag,
    )

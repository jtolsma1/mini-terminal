import os
from datetime import datetime
import pandas as pd
import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
from api_fetch import (
    get_quote_data,
    get_income_statement_data,
    compute_fields_not_in_api,
    combine_data_into_dataframe
)

load_dotenv()
api_url_root = os.getenv("API_URL_ROOT")
api_key = os.getenv("API_KEY")

# disabled; all logging now in MongoDB
# log_path_root = os.path.join(os.getenv("PROJECT_ROOT"),"/logs")

@st.cache_resource
def initiate_mongo_client():
    client = MongoClient("mongodb://mongodb:27017")
    db = client["mini_terminal"]
    collection = db["query_collection_log"]
    return collection

collection = initiate_mongo_client()

try:
    collection.database.client.admin.command("ping")
    st.sidebar.success("MongoDB connected")
except Exception as e:
    st.sidebar.error(f"MongoDB connection failed: {e}")

if not api_url_root:
    st.error("Error: API url root not found in .env")
    st.stop()

if not api_key:
    st.error("Error: API key not found in .env")
    st.stop()

# if not log_path_root:
#     st.error("Error: file path for logs not found in .env")    
#     st.stop()

st.set_page_config(page_title = "Mini Financial Terminal",layout = "wide")

st.title("Mini Financial Terminal")

# Function calls with cache
@st.cache_data(ttl=60*60) # 1 hour cache
def cached_get_quote_data(symbol,api_url_root,api_key,quote_cache_flag):
    quote_cache_flag["ran"] = True
    return get_quote_data(symbol,api_url_root,api_key)
                          
@st.cache_data(ttl=24*60*60) # 24 hour cache
def cached_get_income_statement_data(symbol,api_url_root,api_key,income_cache_flag):
    income_cache_flag["ran"] = True
    return get_income_statement_data(symbol,api_url_root,api_key)

# UI
symbol = st.text_input(
    "Ticker (1-5 Characters Permitted)",
    value = "",
    help = "Example: AAPL. Must be 5 or fewer characters. Capitalization is applied automatically."
).upper().strip()

col1, col2 = st.columns([1,6])
with col1:
    run = st.button("Get Financial Data",type = "primary")

with col2:
    if symbol == "":
        st.info("Enter a 4-character ticker, then click Get Finanical Data.")
    elif len(symbol) > 5:
        st.warning(
        f"Ticket must be 5 or fewer characters. You entered {len(symbol)}."
        )

if run:
    if len(symbol) > 5:
        st.error("Cannot run: ticker must be fewer than 5 characters.")
        st.stop()
    
    with st.spinner(f"Fetching financial data for {symbol}..."):
        quote_cache_flag = {"ran":False}
        income_cache_flag = {"ran":False}
        quote_data = cached_get_quote_data(symbol,api_url_root,api_key,quote_cache_flag)
        income_statement_data = cached_get_income_statement_data(symbol,api_url_root,api_key,income_cache_flag)
        other_data = compute_fields_not_in_api(
            quote_data,
            income_statement_data
            )
        df = combine_data_into_dataframe(
            quote_data=quote_data,
            income_statement_data=income_statement_data,
            other_data=other_data
        )

        quote_api_success = False
        income_api_success = False
        if quote_data != {}:
            quote_api_success = True
        if income_statement_data != {}:
            income_api_success = True

        # log the query in Mongo
        collection.insert_one({
            "symbol":symbol,
            "request_datetime":pd.Timestamp.now(tz = 'America/Los_Angeles'),
            "quote_api_sucess":quote_api_success,
            "income_api_success":income_api_success,
            "quote_from_cache":not quote_cache_flag["ran"],
            "income_statement_from_cache":not income_cache_flag["ran"]
        })

    st.subheader(f"{symbol} Latest Financial Data")

    st.dataframe(df,width ="stretch")

    with st.expander("For admins: raw API outputs"):
        st.write({
            "quote data":quote_data,
            "income statement data":income_statement_data
        }
        )

    with st.sidebar:
        st.header("Cache controls")
        if st.button("Clear Cached Data"):
            st.cache_data.clear()
            st.success("Cache cleared - click Run again to fetch new data.")

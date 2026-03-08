import os
import streamlit as st
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

if not api_url_root:
    st.error("Error: API url root not found in .env")
    st.stop()

if not api_key:
    st.error("Error: API key not found in .env")
    st.stop()
    

st.set_page_config(page_title = "Mini Financial Terminal",layout = "wide")

st.title("Mini Financial Terminal")

# Function calls with cache
@st.cache_data(ttl=60*60) # 1 hour cache
def cached_get_quote_data(symbol,api_url_root,api_key):
    return get_quote_data(symbol,api_url_root,api_key)

@st.cache_data(ttl=24*60*60) # 24 hour cache
def cached_get_income_statement_data(symbol,api_url_root,api_key):
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
        quote_data = cached_get_quote_data(symbol,api_url_root,api_key)
        income_statement_data = cached_get_income_statement_data(symbol,api_url_root,api_key)
        other_data = compute_fields_not_in_api(
            quote_data,
            income_statement_data
            )
        df = combine_data_into_dataframe(
            quote_data=quote_data,
            income_statement_data=income_statement_data,
            other_data=other_data
        )
    
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

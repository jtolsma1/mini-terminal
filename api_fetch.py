import os
import time
import pandas as pd
import requests


API_URL_ROOT = "https://financialmodelingprep.com/stable/"
api_key = os.environ["API_KEY"]

def call_api(symbol,api,items_to_return):
    """
    Generalized function for calling the APIs at Financial Modeling Prep (FMP)
    @param symbol: ticker symbol for public company
    @param api: URL slug for accessing a particular API within FMP
    @param items_to_return: list of items to extract from the API output
    @return: dictionary of API responses (labels and values)
    """
    api = api.lower().strip()
    symbol = symbol.upper().strip()

    if api not in ["quote","income-statement"]:
        raise ValueError("'quote' and 'income-statement' are only APIs currently supported")
    else:
        success = False
        attempts = 2
        wait_secs = 5

        url = os.path.join(API_URL_ROOT,api)
        print(f"Fetching {api.replace("-"," ")} from {url}")
        for attempt in range(attempts):
            response = requests.get(
                url = url,
                params = {"symbol":symbol,"apikey":api_key}
            )

            if response.status_code == 200 :
                success = True
                response_dict = response.json()[0]
                break
            else:
                print(f"Retry attempt {attempt+1} of {attempts} for {symbol} at {url}...")
                time.sleep(wait_secs)
        
    if not success:
        return {}

    else:
        print(f"Response received with length {len(response_dict)}")
            
        if items_to_return is None:
            return response_dict
        else:
            return {k:v for k,v in response_dict.items() if k in items_to_return}
    
def get_quote_data(symbol):
    """
    Get share price quote information from the Financial Modeling Prep API
    @param symbol: ticker symbol for public company
    @return: API output from FPI stock quote API
    """
    api = "quote"
    items_to_return = ["symbol","name","price","marketCap"]
    return call_api(symbol,api,items_to_return)

def get_income_statement_data(symbol):
    """
    Get income statemnt information from the Financial Modeling Prep API
    @param symbol: ticker symbol for public company
    @return: API output from FPI income statement API
    """
    api = "income-statement"
    items_to_return = [
        "reportedCurrency",
        "fiscalYear",
        "revenue",
        "netIncome",
        "eps",
    ]
    return call_api(symbol,api,items_to_return)

def compute_fields_not_in_api(quote_data,income_statement_data):
    """
    To prevent an unnecessary API call, compute metrics like PE ratio using exsting data
    @param quote_data: data obtained from FMP stock quote API
    @param income_statement_data: data obtained from FMP income statement API
    @return: computed outputs as dictioanry
    """
    try:
        pe_ratio = float(quote_data["price"]) / float(income_statement_data["eps"])
        other_data = {"pe_ratio":pe_ratio}
    except:
        other_data = {}
    return other_data

def combine_data_into_dataframe(quote_data,income_statement_data,other_data):
    """
    Build a dataframe from the API outputs that is suitable for Streamlit dash
    @param quote_data: data obtained from FMP stock quote API
    @param income_statement_data: data obtained from FMP income statement API
    @param other_data: any data computed from API outputs
    @return: dataframe to be served in Streamlit dash
    """

    pretty_names = {
        "symbol":"Symbol",
        "name":"Company Name",
        "price":"Share Price",
        "marketCap":"Market Cap",
        "reportedCurrency":"Reported Currency",
        "fiscalYear":"Latest Completed Fiscal Year",
        "revenue":"Total Revenue",
        "netIncome":"Total Net Income",
        "eps":"Earnings Per Share",
        "pe_ratio":"Price to Earnings Ratio"
    }

    combined_dict = quote_data | income_statement_data | other_data
    df = pd.DataFrame(combined_dict,index = ["api_output"]).transpose().rename(pretty_names,axis = 0)

    
    return df

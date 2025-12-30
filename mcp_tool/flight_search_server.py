import json
import sys
import os
import logging
import asyncio
import inspect
from typing import Annotated
from pydantic import BaseModel, Field
from collections import defaultdict
 
# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stderr, redirect_stdout
from bs4 import BeautifulSoup
from seleniumbase import SB
from mcp.server.fastmcp import FastMCP
# --- Configure Logging to use STDERR ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr 
)
logger = logging.getLogger(__name__)
try:
    from scrapper.mmt import scrap_extract as mmt
    from scrapper.ixigo import scrap_extract as ixigo
   # scrapper/mmt/scrap_extract.py 
    # from scrapper.mmt import data_extraction as mmt_data_extraction

    # from scrapper.ixigo import ixigo_scrap
    # from scrapper.ixigo import data_extraction as ixigo_data_extraction

    # from scrapper.expedia import expedia_scrap
    # from scrapper.expedia import data_extraction as expedia_data_extraction

    # functions = [name for name, obj in inspect.getmembers(mmt_scrap) if inspect.isfunction(obj)]
    # logger.info(f"Functions found in mmt_scrap: {functions}")
    
     
except Exception as e:
    print(f"Error loading module: {e}")
 

mcp = FastMCP("FlightSearch")


# Thread pool executor for blocking operations
executor = ThreadPoolExecutor(max_workers=2)

def convert_to_date_std(date_string: str) -> datetime:
    """
    Attempts to parse a date string using a list of common formats.
    """
    formats = [
        "%d/%m/%Y",  # 28/12/2025
        "%Y-%m-%d",  # 2025-12-28 (ISO)
        "%d-%m-%Y",  # 28-12-2025
        "%Y/%m/%d",  # 2025/12/28
        "%d %b %Y",  # 28 Dec 2025
        "%B %d, %Y", # December 28, 2025
    ]
    
    # Clean the string (remove extra whitespace)
    date_string = date_string.strip()
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
            
    raise ValueError(f"Format not recognized for date: {date_string}")

# class FlightSearchInput(BaseModel):
#     origin: str = Field( description="IATA airport code for origin (e.g., 'LKO')")
#     destination: str = Field( description="IATA airport code for destination (e.g., 'IXL')")
#     travel_date: str = Field( description="Travel date in DD/MM/YYYY format (e.g., '28/12/2025')")
#     source: list = Field(default=["all"], description="a list containing following options mmt, expedia,ixigo  or all ")


# @mcp.tool(
#     name="search_flights", 
#     description="Searches for flights on mmt, ixigo, and expedia concurrently."
# )
# async def search_flights(
#     origin: str = Field(description="IATA airport code for origin (e.g., 'LKO')"),
#     destination: str = Field(description="IATA airport code for destination (e.g., 'IXL')"),
#     travel_date: str = Field(description="Travel date in DD/MM/YYYY format (e.g., '28/12/2025')"),
#     source: list = Field(default=["all"], description="List containing: mmt, expedia, ixigo, or all")
# ) -> str:
#     """
#     Searches for available flights between two airports across multiple platforms.
#     All logging and print statements are redirected to stderr to protect the MCP JSON-RPC stream.
#     """
#     logger.info(f"Initiating concurrent flight search: {origin} to {destination} via {source}")
    
@mcp.tool(
    name="search_flights", 
    description="Searches for flights on multiple platforms concurrently using a unified executor."
)
async def search_flights(
    origin: str = Field(description="IATA airport code for origin (e.g., 'LKO')"),
    destination: str = Field(description="IATA airport code for destination (e.g., 'IXL')"),
    travel_date: str = Field(description="Travel date in DD/MM/YYYY format (e.g., '28/12/2025')"),
    source: list = Field(default=["all"], description="List containing: mmt, expedia, ixigo, or all")
) -> str:
    """
    Orchestrates flight searches by mapping sources to the scrap_extract.execute function.
    """
    logger.info(f"Unified Search: {origin} -> {destination} | Date: {travel_date} | Sources: {source}")
    
    try:
        # 1. Standardize date for logic
        base_date_obj = convert_to_date_std(travel_date)
        loop = asyncio.get_event_loop()

        # 2. Unified Registry
        # We store the function reference and the specific format needed for that source
        registry = {
            "mmt": {
                "func": mmt.execute,
                "dateFormat": "%d/%m/%Y"
            },
            "ixigo": {
                "func": ixigo.execute,
                "dateFormat": "%d%m%Y"
            },
            # "expedia": {
            #     "func": scrap_extract.execute,
            #     "dateFormat": "%d/%m/%Y"
            # }
        }

        # 3. Filter requested sources
        keys_to_process = list(registry.keys()) if "all" in source else [s for s in source if s in registry]

        if not keys_to_process:
            return "Error: No valid sources selected."

        # 4. Pipeline helper for concurrent execution
        async def run_provider_task(key):
            # Guard against stdout pollution (prevents MCP crashes from '====' logs)
            with redirect_stdout(sys.stderr), redirect_stderr(sys.stderr):
                try:
                    # Apply the provider-specific date string
                    provider_date_str = base_date_obj.strftime(registry[key]["dateFormat"])
                    
                    logger.info(f"[{key}] Launching execute with date: {provider_date_str}")
                    
                    # Call the unified execute function
                    # We pass 'key' (mmt, ixigo, etc.) so execute() knows which site to hit
                    data = await loop.run_in_executor(
                        executor, 
                        registry[key]["func"], 
                   #    key,           # source_name
                        origin, 
                        destination, 
                        provider_date_str
                    )
                    
                    # Ensure we return a list of flights
                    if data and isinstance(data, list):
                        # Add provider tag if not already present in scrap_extract.execute
                        for flight in data:
                            if "provider" not in flight:
                                flight["provider"] = key
                        return data
                    return []
                    
                except Exception as e:
                    sys.stderr.write(f"[{key}] Task Failed: {str(e)}\n")
                    return []

        # 5. Execute all tasks in parallel
        tasks = [run_provider_task(key) for key in keys_to_process]
        results_nested = await asyncio.gather(*tasks)

        # 6. Flatten nested results into one list
        all_results = [item for sublist in results_nested for item in sublist]
         
        flight_data_dict = defaultdict(lambda: defaultdict(list))

        # 2. Populate the dictionary from your all_results list
        for flight in all_results:
            # We use flight.get() to safely handle missing keys
            f_no = flight.get('flight_no')
            src = flight.get('source')
            f_no = f_no.replace(" ", "")
            if f_no and src:
                flight_data_dict[f_no][src].append(flight)
            # if i['flight_no'] in flight_data_dict:
            #     flight_data_dict[i['flight_no']].append(i)
            # else:
            #     flight_data_dict[i['flight_no']] = {
            #         i['source']:[i]
            #     }

        
        if not flight_data_dict:
            return "No flight data returned from any provider."
        logger.info(flight_data_dict)
        return json.dumps(flight_data_dict, indent=2)
        
    except Exception as e:
        logger.error(f"Fatal tool error: {e}", exc_info=True)
        return f"Error executing search: {str(e)}"


    # try:
    #     # 1. Standardize the date
    #     required_date_format = convert_to_date_std(travel_date)
    #     travel_date_str = required_date_format#.strftime("%d/%m/%Y")
        
    #     loop = asyncio.get_event_loop()

    #     # 2. Define the Registry for Scrapers and Parsers
    #     registry = {

    #         # "ixigo": {
    #         #     "scrap": ixigo_scrap.scrap_data,
    #         #     "parse": ixigo_data_extraction.parse_flight_data,
    #         #     "dateFormat": "%d%m%Y" #15122025
    #         # },
    #         "mmt": scrap_extract.execute,
            
    #         # "expedia": {
    #         #     "scrap": expedia_scrap.scrap_data,
    #         #     "parse": expedia_data_extraction.parse_flight_data,
    #         #     "dateFormat": "%d/%m/%Y"
    #         # }
    #     }

    #     # 3. Determine which sources to process
    #     keys_to_process = list(registry.keys()) if "all" in source else [s for s in source if s in registry]

    #     if not keys_to_process:
    #         return "Error: No valid sources provided. Please use mmt, ixigo, or expedia."

    #     # 4. Define the Internal Pipeline for a single source
    #     async def run_pipeline_for_source(key):
    #         # This context manager is the fix for your Pydantic/JSON errors
    #         # It forces any 'print' or '====' lines to go to stderr instead of stdout
    #         with redirect_stdout(sys.stderr), redirect_stderr(sys.stderr):
    #             try:
    #                 # Execute Scraping
    #                 provider_date_str = required_date_format.strftime(registry[key]["dateFormat"])
    #                 logger.info(f"[{key}] Using date format: {provider_date_str}")
    #                 await loop.run_in_executor(
    #                     executor, 
    #                     registry[key]["scrap"], 
    #                     origin, 
    #                     destination, 
    #                     provider_date_str
    #                 )
                    
    #                 # Execute Parsing immediately after scrape completes for this specific key
    #                 logger.info(f"[{key}] Scraping finished. Starting parser...")
    #                 data = await loop.run_in_executor(
    #                     executor, 
    #                     registry[key]["parse"]
    #                 )
                    
    #                 if data and isinstance(data, list):
    #                     for flight in data:
    #                         flight["provider"] = key
    #                     return data
    #                 return []
                    
    #             except Exception as e:
    #                 sys.stderr.write(f"Error in {key} pipeline: {str(e)}\n")
    #                 return []

    #     # 5. Execute all selected pipelines concurrently
    #     tasks = [run_pipeline_for_source(key) for key in keys_to_process]
        
    #     # Results will be a list of lists: [[mmt_flights], [ixigo_flights], ...]
    #     results_nested = await asyncio.gather(*tasks)

    #     # 6. Flatten and Return
    #     all_results = [item for sublist in results_nested for item in sublist]

    #     if not all_results:
    #         return "No flights were found from the requested sources."
            
    #     return json.dumps(all_results, indent=2)
        
    # except Exception as e:
    #     # Ensure the final error message is also logged to stderr
    #     logger.error(f"Fatal tool error: {e}", exc_info=True)
    #     return f"Error executing search: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
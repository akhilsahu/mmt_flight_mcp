import sys
import os
import logging
import asyncio
import inspect
from typing import Annotated

from pydantic import BaseModel, Field
# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
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
    from scrapper.mmt import mmt_scrap
    from scrapper.mmt import data_extraction as mmt_data_extraction
    
    from scrapper.ixigo import ixigo_scrap
    from scrapper.ixigo import data_extraction as ixigo_data_extraction

    from scrapper.expedia import expedia_scrap
    from scrapper.expedia import data_extraction as expedia_data_extraction

    functions = [name for name, obj in inspect.getmembers(mmt_scrap) if inspect.isfunction(obj)]
    logger.info(f"Functions found in mmt_scrap: {functions}")
    
     
except Exception as e:
    print(f"Error loading module: {e}")

#from scrapper.mmt.mmt_scrap import scrap_sb_sync
#from scrapper.mmt.data_extraction import get_flights

registry = {
            "mmt": {
                "scrap": mmt_scrap.scrap_data,
                "parse": mmt_data_extraction.parse_flight_data
            },
            "ixigo": {
                "scrap": ixigo_scrap.scrap_data,
                "parse": ixigo_data_extraction.parse_flight_data
            },
            "expedia": {
                "scrap": expedia_scrap.scrap_data,
                "parse": expedia_data_extraction.parse_flight_data
            }
        }


mcp = FastMCP("FlightSearch")

# --- Configuration ---
# HTML_FILE_PATH = "./downloads/ss/mmt_res.html" 
# OUTPUT_CSV_PATH = "flight_data_extracted.csv"

# # --- Selectors ---
# FLIGHT_LISTING_SELECTOR = 'div[data-test*=component-clusterItem]'
# AIRLINE_SELECTOR = 'p[class*="airlineName"]'
# TIME_CITY_GROUP_SELECTOR = 'p[class*="flightTimeInfo"]'
# START_DURATION_SELECTOR = 'div[class*="timeInfoLeft"]'
# LAYOVER_DURATION_SELECTOR = 'div[class*="stop-info"]'
# END_DURATION_SELECTOR = 'div[class*="timeInfoRight"]'
# PRICE_SELECTOR = 'div[class*="priceSection"]'

# Thread pool executor for blocking operations
executor = ThreadPoolExecutor(max_workers=2)

# def scrap_sb_sync(origin, destination, travel_date):
#     """Synchronous scraping function to run in thread"""
#     try:
#         with SB(uc=True, test=True, xvfb=True) as sb:
#             url = f"https://www.makemytrip.com/flight/search?itinerary={origin}-{destination}-{travel_date}&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E&lang=eng"
#             sb.activate_cdp_mode(url)
            
#             sb.sleep(5)
#             try:
#                 sb.click('button.priceLockProCtaButton.whiteText')
#             except Exception:
#                 logger.warning("Popup button not found or already closed.")
                
#             sr = sb.get_page_source()
            
#             import os
#             os.makedirs(os.path.dirname(HTML_FILE_PATH), exist_ok=True)
            
#             with open(HTML_FILE_PATH, "w", encoding="utf-8") as f:
#                 f.write(sr)
#             logger.info("Scraping completed successfully.")
#             sb.quit()
#             return True
#     except Exception as e:
#         logger.error(f"Error during scraping: {e}")
#         raise e

# def scrap_flight_data(origin, destination, travel_date,url=None):
#     """Synchronous scraping function to run in thread"""
#     try:
#         with SB(uc=True, test=True, xvfb=True) as sb:
#             #https://www.ixigo.com/search/result/flight?from=BOM&to=DEL&date=15122025&adults=1&children=0&infants=0&class=e&source=Search+Form
#             url = f"https://www.makemytrip.com/flight/search?itinerary={origin}-{destination}-{travel_date}&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E&lang=eng"
#             sb.activate_cdp_mode(url)
            
#             sb.sleep(5)
#             try:
#                 sb.click('button.priceLockProCtaButton.whiteText')
#             except Exception:
#                 logger.warning("Popup button not found or already closed.")
                
#             sr = sb.get_page_source()
            
#             import os
#             os.makedirs(os.path.dirname(HTML_FILE_PATH), exist_ok=True)
            
#             with open(HTML_FILE_PATH, "w", encoding="utf-8") as f:
#                 f.write(sr)
#             logger.info("Scraping completed successfully.")
#             sb.quit()
#             return True
#     except Exception as e:
#         logger.error(f"Error during scraping: {e}")
#         raise e

# def get_flights(origin, destination, travel_date):
#     """Parses the scraped HTML to extract flight data."""
#     try:
#         with open(HTML_FILE_PATH, 'r', encoding='utf-8') as f:
#             html_content = f.read()
#     except FileNotFoundError:
#         logger.error(f"Error: The file '{HTML_FILE_PATH}' was not found.")
#         return []
#     except Exception as e:
#         logger.error(f"Error reading file: {e}")
#         return []

#     soup = BeautifulSoup(html_content, 'html.parser')
#     flight_data = []
#     flight_cards = soup.select(FLIGHT_LISTING_SELECTOR)

#     if not flight_cards:
#         logger.warning(f"No flight cards found using selector: {FLIGHT_LISTING_SELECTOR}")
#         return []

#     logger.info(f"Found {len(flight_cards)} potential flight listings. Extracting data...")

#     for flight_card in flight_cards:
#         try:
#             airline_element = flight_card.select_one(AIRLINE_SELECTOR)
#             airline = airline_element.text.strip() if airline_element else "N/A"

#             time_city_groups = flight_card.select(TIME_CITY_GROUP_SELECTOR)
#             if len(time_city_groups) >= 2:
#                 dep_time = time_city_groups[0].text.strip()
#                 arr_time = time_city_groups[-1].text.strip()
#             else:
#                 dep_time, arr_time = 'N/A', 'N/A'

#             departure_element = flight_card.select_one(START_DURATION_SELECTOR)
#             departure_city = "N/A"
#             departure_time_p = "N/A"
#             if departure_element:
#                 departure_time_p = departure_element.find('p').text if departure_element.find('p') else "N/A"
#                 dep_city_tag = departure_element.find('p', class_='blackText')
#                 departure_city = dep_city_tag.text if dep_city_tag else "N/A"
            
#             layover_element = flight_card.select_one(LAYOVER_DURATION_SELECTOR)
#             layover_duration = "N/A"
#             layover_city = "N/A"
#             if layover_element:
#                 layover_duration = layover_element.find('p').text if layover_element.find('p') else "N/A"
#                 lay_city_tag = layover_element.find('p', class_='flightsLayoverInfo')
#                 layover_city = lay_city_tag.text if lay_city_tag else "N/A"

#             arrival_element = flight_card.select_one(END_DURATION_SELECTOR)
#             arrival_city = "N/A"
#             arrival_time_p = "N/A"
#             if arrival_element:
#                 arrival_time_p = arrival_element.find('p').text if arrival_element.find('p') else "N/A"
#                 arr_city_tag = arrival_element.find('p', class_='blackText')
#                 arrival_city = arr_city_tag.text if arr_city_tag else "N/A"

#             price_element = flight_card.select_one(PRICE_SELECTOR)
#             price_text = "N/A"
#             if price_element:
#                 price_span = price_element.find("span")
#                 price_text = price_span.text.strip() if price_span else "N/A"
            
#             offers_tag = flight_card.find("p", class_="alertMsg appendBottom10 appendTop10 textCenter")
#             offers = offers_tag.text if offers_tag else "N/A"

#             flight_data.append({
#                 'Airline': airline,
#                 'Departure_Time': departure_time_p,
#                 'Departure_City': departure_city,
#                 'Arrival_Time': arrival_time_p,
#                 'Arrival_City': arrival_city,
#                 'Layover_Duration': layover_duration,
#                 'Layover_City': layover_city,
#                 'Price': price_text,
#                 'Offers': offers
#             })

#         except Exception as e:
#             logger.warning(f"Skipping a flight card due to error: {e}")
#             continue

#     return flight_data

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

class FlightSearchInput(BaseModel):
    origin: str = Field( description="IATA airport code for origin (e.g., 'LKO')")
    destination: str = Field( description="IATA airport code for destination (e.g., 'IXL')")
    travel_date: str = Field( description="Travel date in DD/MM/YYYY format (e.g., '28/12/2025')")
    source: list = Field(default=["all"], description="a list containing following options mmt, expedia,ixigo  or all ")


# @mcp.tool( name="search_mmt_flights", description="Searches for available flights between two airports on a specific date using give source website expedia,ixigo or mmt(Makemytrip website) or all if source is all.")
# async def search_flights(
#     origin: str = Field( description="IATA airport code for origin (e.g., 'LKO')"),
#     destination: str = Field( description="IATA airport code for destination (e.g., 'IXL')"),
#     travel_date: str = Field( description="Travel date in DD/MM/YYYY format (e.g., '28/12/2025')"),
#     source: list = Field(default=["all"], description="a list containing following options mmt, expedia,ixigo  or all ")


#     # origin: Annotated[str , Field( description="IATA airport code for origin (e.g., 'LKO')")],
#     # destination: Annotated[str, Field( description="IATA airport code for destination (e.g., 'IXL')")],
#     # travel_date: Annotated [ str , Field( description="Travel date in DD/MM/YYYY format (e.g., '28/12/2025')")],
#     # source: Annotated[list , Field(default=["all"], description="a list containing following options mmt, expedia,ixigo  or all ")]
# ) -> str:
#     """
#     Searches for available flights between two airports on a specific date .
#     IMPORTANT: The travel_date MUST be in DD/MM/YYYY format (e.g., '28/12/2025').
#     Do NOT use anyother format like YYYY-MM-DD.
#     Args:
#         source : a list containing following options mmt, expedia,ixigo  or all 
#         origin: The IATA airport code (e.g., 'LKO').
#         destination: The IATA airport code (e.g., 'IXL').
#         travel_date: The date of travel in DD/MM/YYYY format.
        
#     """
#     logger.info(f"Tool called: origin={origin}, dest={destination}, date={travel_date}, source={source} ")
    
#     try:
#         # Run the blocking scraping in a thread pool
        

#         required_date_format = convert_to_date_std(travel_date)
#         travel_date = required_date_format.strftime("%d/%m/%Y")
#         loop = asyncio.get_event_loop()
#         with redirect_stdout(sys.stderr):
#             await loop.run_in_executor(
#                 executor, 
#                 mmt_scrap.scrap_data, 
#                 origin, 
#                 destination, 
#                 travel_date
#             )
        
#         # Parse results (this is fast, can run in main thread)
#         results = mmt_data_extraction.read_and_parse_flight_data()
        
#         if not results:
#             return "No flights found or error occurred during extraction."
            
#         import json
#         return json.dumps(results, indent=2)
        
#     except Exception as e:
#         logger.error(f"Fatal tool error: {e}", exc_info=True)
#         return f"Error executing search: {str(e)}"

@mcp.tool(
    name="search_flights", 
    description="Searches for flights on mmt, ixigo, or expedia concurrently."
)
async def search_flights(
    origin: str = Field(description="IATA airport code for origin (e.g., 'LKO')"),
    destination: str = Field(description="IATA airport code for destination (e.g., 'IXL')"),
    travel_date: str = Field(description="Travel date in DD/MM/YYYY format (e.g., '28/12/2025')"),
    source: list = Field(default=["all"], description="List containing: mmt, expedia, ixigo, or all")
) -> str:
    logger.info(f"Concurrent search: {origin} to {destination} on {travel_date} via {source}")
    
    try:
        required_date_format = convert_to_date_std(travel_date)
        travel_date_str = required_date_format.strftime("%d/%m/%Y")
        loop = asyncio.get_event_loop()

        registry = {
            "mmt": {
                "scrap": mmt_scrap.scrap_data,
                "parse": mmt_data_extraction.parse_flight_data
            },
            # "ixigo": {
            #     "scrap": ixigo_scrap.scrap_data,
            #     "parse": ixigo_data_extraction.parse_flight_data
            # },
            # "expedia": {
            #     "scrap": expedia_scrap.scrap_data,
            #     "parse": expedia_data_extraction.parse_flight_data
            # }
        }

        keys_to_process = list(registry.keys()) if "all" in source else [s for s in source if s in registry]

        if not keys_to_process:
            return "Error: No valid sources provided."

        # Define a task for a single source: Scrape then Parse
        async def fetch_source_data(key):
            try:
                # Run Scraper
                await loop.run_in_executor(
                    executor, 
                    registry[key]["scrap"], 
                    origin, 
                    destination, 
                    travel_date_str
                )
                # Run Parser
                data = await loop.run_in_executor(executor, registry[key]["parse"])
                
                if data and isinstance(data, list):
                    for flight in data:
                        flight["provider"] = key
                    return data
                return []
            except Exception as e:
                logger.error(f"Error processing {key}: {e}")
                return []

        # Trigger all tasks concurrently
        tasks = [fetch_source_data(key) for key in keys_to_process]
        results_nested = await asyncio.gather(*tasks)

        # Flatten the list of lists
        all_results = [item for sublist in results_nested for item in sublist]

        if not all_results:
            return "No flights found across the selected sources."
            
        import json
        return json.dumps(all_results, indent=2)
        
    except Exception as e:
        logger.error(f"Fatal tool error: {e}", exc_info=True)
        return f"Error executing search: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
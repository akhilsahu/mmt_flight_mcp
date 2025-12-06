import sys
import logging
import asyncio
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

mcp = FastMCP("FlightSearch")

# --- Configuration ---
HTML_FILE_PATH = "./independent/ss/mmt_res.html" 
OUTPUT_CSV_PATH = "flight_data_extracted.csv"

# --- Selectors ---
FLIGHT_LISTING_SELECTOR = 'div[data-test*=component-clusterItem]'
AIRLINE_SELECTOR = 'p[class*="airlineName"]'
TIME_CITY_GROUP_SELECTOR = 'p[class*="flightTimeInfo"]'
START_DURATION_SELECTOR = 'div[class*="timeInfoLeft"]'
LAYOVER_DURATION_SELECTOR = 'div[class*="stop-info"]'
END_DURATION_SELECTOR = 'div[class*="timeInfoRight"]'
PRICE_SELECTOR = 'div[class*="priceSection"]'

# Thread pool executor for blocking operations
executor = ThreadPoolExecutor(max_workers=2)

def scrap_sb_sync(origin, destination, travel_date):
    """Synchronous scraping function to run in thread"""
    try:
        with SB(uc=True, test=True, xvfb=True) as sb:
            url = f"https://www.makemytrip.com/flight/search?itinerary={origin}-{destination}-{travel_date}&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E&lang=eng"
            sb.activate_cdp_mode(url)
            
            sb.sleep(9)
            try:
                sb.click('button.priceLockProCtaButton.whiteText')
            except Exception:
                logger.warning("Popup button not found or already closed.")
                
            sr = sb.get_page_source()
            
            import os
            os.makedirs(os.path.dirname(HTML_FILE_PATH), exist_ok=True)
            
            with open(HTML_FILE_PATH, "w", encoding="utf-8") as f:
                f.write(sr)
            logger.info("Scraping completed successfully.")
            sb.quit()
            return True
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        raise e

def get_flights(origin, destination, travel_date):
    """Parses the scraped HTML to extract flight data."""
    try:
        with open(HTML_FILE_PATH, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        logger.error(f"Error: The file '{HTML_FILE_PATH}' was not found.")
        return []
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    flight_data = []
    flight_cards = soup.select(FLIGHT_LISTING_SELECTOR)

    if not flight_cards:
        logger.warning(f"No flight cards found using selector: {FLIGHT_LISTING_SELECTOR}")
        return []

    logger.info(f"Found {len(flight_cards)} potential flight listings. Extracting data...")

    for flight_card in flight_cards:
        try:
            airline_element = flight_card.select_one(AIRLINE_SELECTOR)
            airline = airline_element.text.strip() if airline_element else "N/A"

            time_city_groups = flight_card.select(TIME_CITY_GROUP_SELECTOR)
            if len(time_city_groups) >= 2:
                dep_time = time_city_groups[0].text.strip()
                arr_time = time_city_groups[-1].text.strip()
            else:
                dep_time, arr_time = 'N/A', 'N/A'

            departure_element = flight_card.select_one(START_DURATION_SELECTOR)
            departure_city = "N/A"
            departure_time_p = "N/A"
            if departure_element:
                departure_time_p = departure_element.find('p').text if departure_element.find('p') else "N/A"
                dep_city_tag = departure_element.find('p', class_='blackText')
                departure_city = dep_city_tag.text if dep_city_tag else "N/A"
            
            layover_element = flight_card.select_one(LAYOVER_DURATION_SELECTOR)
            layover_duration = "N/A"
            layover_city = "N/A"
            if layover_element:
                layover_duration = layover_element.find('p').text if layover_element.find('p') else "N/A"
                lay_city_tag = layover_element.find('p', class_='flightsLayoverInfo')
                layover_city = lay_city_tag.text if lay_city_tag else "N/A"

            arrival_element = flight_card.select_one(END_DURATION_SELECTOR)
            arrival_city = "N/A"
            arrival_time_p = "N/A"
            if arrival_element:
                arrival_time_p = arrival_element.find('p').text if arrival_element.find('p') else "N/A"
                arr_city_tag = arrival_element.find('p', class_='blackText')
                arrival_city = arr_city_tag.text if arr_city_tag else "N/A"

            price_element = flight_card.select_one(PRICE_SELECTOR)
            price_text = "N/A"
            if price_element:
                price_span = price_element.find("span")
                price_text = price_span.text.strip() if price_span else "N/A"
            
            offers_tag = flight_card.find("p", class_="alertMsg appendBottom10 appendTop10 textCenter")
            offers = offers_tag.text if offers_tag else "N/A"

            flight_data.append({
                'Airline': airline,
                'Departure_Time': departure_time_p,
                'Departure_City': departure_city,
                'Arrival_Time': arrival_time_p,
                'Arrival_City': arrival_city,
                'Layover_Duration': layover_duration,
                'Layover_City': layover_city,
                'Price': price_text,
                'Offers': offers
            })

        except Exception as e:
            logger.warning(f"Skipping a flight card due to error: {e}")
            continue

    return flight_data

@mcp.tool()
async def search_flights(origin: str, destination: str, travel_date: str) -> str:
    """
    Searches for available flights between two airports on a specific date.
    
    Args:
        origin: The IATA airport code (e.g., 'LKO').
        destination: The IATA airport code (e.g., 'IXL').
        travel_date: The date of travel in DD/MM/YYYY format.
    """
    logger.info(f"Tool called: origin={origin}, dest={destination}, date={travel_date}")
    
    try:
        # Run the blocking scraping in a thread pool
        loop = asyncio.get_event_loop()
        with redirect_stdout(sys.stderr):
            await loop.run_in_executor(
                executor, 
                scrap_sb_sync, 
                origin, 
                destination, 
                travel_date
            )
        
        # Parse results (this is fast, can run in main thread)
        results = get_flights(origin, destination, travel_date)
        
        if not results:
            return "No flights found or error occurred during extraction."
            
        import json
        return json.dumps(results, indent=2)
        
    except Exception as e:
        logger.error(f"Fatal tool error: {e}", exc_info=True)
        return f"Error executing search: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
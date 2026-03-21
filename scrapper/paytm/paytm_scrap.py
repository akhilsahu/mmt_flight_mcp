import json
import logging
import os
import sys
from datetime import datetime

import requests

from scrapper.scrap_config import HTML_FILE_PATH_PAYTM

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


def _format_travel_date(travel_date: str) -> str:
    """
    Accepts:
    - YYYYMMDD (Paytm format)
    - DD/MM/YYYY
    - DDMMYYYY
    Returns YYYYMMDD.
    """
    if not travel_date:
        raise ValueError("travel_date is required")

    if len(travel_date) == 8 and travel_date.isdigit():
        # Heuristic: if starts with year-like prefix keep as-is.
        if travel_date.startswith(("19", "20")):
            return travel_date
        return datetime.strptime(travel_date, "%d%m%Y").strftime("%Y%m%d")

    if "/" in travel_date:
        return datetime.strptime(travel_date, "%d/%m/%Y").strftime("%Y%m%d")

    raise ValueError("Unsupported travel_date format")


def write_to_file(content, filename="./scrapper/paytm_res.html", mode="a"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, mode, encoding="utf-8") as f:
        f.write(content)


def scrap_data(origin="LKO", destination="DEL", travel_date="20260401", uniquas=None):
    """
    Format for paytm:
    - travel_date="20260401" (preferred)
    - travel_date="01/04/2026"
    - travel_date="01042026"
    """
    logger.info(f"Scraping paytm for {origin} to {destination} on {travel_date}")
    formatted_date = _format_travel_date(travel_date)

    url = "https://travel.paytm.com/api/flights/v3/search"
    params = {
        "accept": "combination",
        "adults": 1,
        "application_platform": "dweb",
        "children": 0,
        "class": "E",
        "client": "web",
        "cohort": "null",
        "departureDate": formatted_date,
        "destination": destination,
        "enable": json.dumps({
            "handBaggageFare": True,
            "paxWiseConvFee": True,
            "minirules": True
        }),
        "infants": 0,
        "isH5": "true",
        "origin": origin,
        "productFlow": "null",
        "progressiveLoadingEnabled": "false",
        "retryCount": 1,
        "userType": "null",
        "version": 2,
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://travel.paytm.com/flights/",
    }

    data = {}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
        else:
            logger.warning(f"Paytm request failed. Status: {response.status_code}")
            logger.warning(response.text[:500])

        write_to_file(
            json.dumps(data),
            filename=HTML_FILE_PATH_PAYTM.format(unqiuas=uniquas),
            mode="w"
        )
        return data
    except Exception as e:
        logger.error(f"Error while scraping Paytm: {e}")
        return None


if __name__ == "__main__":
    scrap_data()

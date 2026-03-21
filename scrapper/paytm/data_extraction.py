import json
import logging
import sys

from scrapper.scrap_config import HTML_FILE_PATH_PAYTM

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


def _flight_type_from_hops(hops_count: int) -> str:
    if hops_count <= 1:
        return "Non-stop"
    if hops_count == 2:
        return "1 Stop"
    return f"{hops_count - 1} Stops"


def parse_flight_data(data, uniquas):
    """Extracts Paytm flight list into project-standard format."""
    flights_data = []

    if not data:
        with open(HTML_FILE_PATH_PAYTM.format(unqiuas=uniquas), "r", encoding="utf-8") as f:
            data = json.loads(f.read())

    flights = (
        data.get("body", {})
        .get("onwardflights", {})
        .get("flights", [])
    )

    for flight in flights:
        all_details = {}
        navigation_details = {}

        hops = flight.get("hops", [])
        first_hop = hops[0] if hops else {}
        layover_city = ""
        if len(hops) > 1:
            layover_points = [hop.get("origin") for hop in hops[1:]]
            layover_city = ", ".join([lp for lp in layover_points if lp])

        price_list = flight.get("price", [])
        first_price = price_list[0] if price_list else {}
        discounts = first_price.get("discounts", {})

        price = first_price.get("totalfare", first_price.get("price"))
        offers = (
            discounts.get("display_text")
            or discounts.get("promo_details", {}).get("supporting_text")
            or ""
        )

        all_details["refundable"] = flight.get("refundable")
        all_details["refundable_text"] = flight.get("refundable_text")
        all_details["fare_sub_type"] = flight.get("fare_sub_type")
        all_details["ttl"] = flight.get("ttl")

        navigation_details = {
            "flight_id": flight.get("flightid"),
            "solution_id": flight.get("solutionId"),
            "provider": first_price.get("provider"),
            "partner": first_price.get("partner"),
            "price_id": first_price.get("priceid"),
        }

        flights_data.append({
            "Airline": flight.get("airline") or first_hop.get("airline"),
            "flight_no": first_hop.get("flightNumber"),
            "Departure_Time": flight.get("departureTimeAirport"),
            "Departure_City": flight.get("origin"),
            "Duration": flight.get("duration"),
            "Arrival_Time": flight.get("arrivalTimeAirport"),
            "Arrival_City": flight.get("destination"),
            "flight_type": _flight_type_from_hops(len(hops)),
            "Layover_Duration": "",
            "Layover_City": layover_city,
            "Price": price,
            "Offers": offers,
            "extra_badges": flight.get("additional_info", {}).get("late_night_flight", ""),
            "source": "paytm",
            "all_details": all_details,
            "navigation_details": navigation_details
        })

    return flights_data


if __name__ == "__main__":
    parse_flight_data(None, None)

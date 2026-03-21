import time

from scrapper.paytm import data_extraction
from scrapper.paytm import paytm_scrap


def execute(origin, destination, travel_date):
    rand_choice = time.time()
    data = paytm_scrap.scrap_data(origin, destination, travel_date, rand_choice)
    parsing_data = data_extraction.parse_flight_data(data, rand_choice)
    return parsing_data


if __name__ == "__main__":
    execute("LKO", "DEL", "20260401")

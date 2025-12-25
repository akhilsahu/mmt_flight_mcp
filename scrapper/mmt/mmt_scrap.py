from seleniumbase import SB
import logging,sys
# --- Configure Logging to use STDERR ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr 
)
logger = logging.getLogger(__name__)

 

# --- Configuration ---
HTML_FILE_PATH = "./scrapper/ss/mmt1_res.html" 
def scrap_sb(origin="LKO", destination="IXL", travel_date="18/11/2025"):
    with SB(uc=True, test=True) as sb:
        url = f"https://www.makemytrip.com/flight/search?itinerary={origin}-{destination}-{travel_date}&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E&lang=eng"
        sb.activate_cdp_mode(url)
        
        sb.sleep(9)
        sb.click('button.priceLockProCtaButton.whiteText')
        sb.get_page_source()
        #sb.save_screenshot('./ss/mmt_res.png', full_page=True)
        sr = sb.get_page_source()
        
        with open("./scrapper/mmt_res.html", "w", encoding="utf-8") as f:
            f.write(sr)
        logger.info("Scraping completed")
        sb.quit()
def scrap_data(origin, destination, travel_date):
    """Synchronous scraping function to run in thread"""
    try:
        with SB(uc=True, test=True, xvfb=True) as sb:
            url = f"https://www.makemytrip.com/flight/search?itinerary={origin}-{destination}-{travel_date}&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E&lang=eng"
            sb.activate_cdp_mode(url)
            
            sb.sleep(5)
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

if __name__ == "__main__":
    scrap_sb()
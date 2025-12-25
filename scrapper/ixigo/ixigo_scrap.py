from seleniumbase import SB
import logging
import sys

from scrapper.mmt.mmt_scrap import scrap_sb
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr 
)
logger = logging.getLogger(__name__)
def scrap_data(origin="LKO", destination="DEL", travel_date="25122025"):
    '''
    Format for mmt: travel_date="18/11/2025"
    Format for ixigo: travel_date=15122025
    '''
    #with SB(uc=True, test=True, headless2=True) as sb:
    with SB(uc=True, test=True) as sb:    
        #url = f"https://www.makemytrip.com/flight/search?itinerary={origin}-{destination}-{travel_date}&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E&lang=eng"
        url = f"https://www.ixigo.com/search/result/flight?from={origin}&to={destination}&date={travel_date}&adults=1&children=0&infants=0&class=e&source=Search+Form"
        sb.set_window_size(1400, 8000)

        sb.activate_cdp_mode(url)
        sb.activate_jquery()
        sb.sleep(12)
        #document.elementFromPoint(2, 5).click();
        sb.execute_script("jQuery, document.elementFromPoint(2, 5).click();")
        #sb.execute_script("document.querySelector('.bg-neutral-60.h-screen.overflow-y-auto').scrollTo(0, 2000);")
        

        # multi_line_script_scroll = """
        #      const scrollStep = 5; // Amount to scroll in each step (pixels)
        #      const scrollIntervalTime = 10; // Time between steps (milliseconds)

        #     function simulateStepByStepScroll() {
        #         const totalPageHeight = document.body.scrollHeight;
        #         const viewportHeight = window.innerHeight;
        #         let currentScrollPosition = window.pageYOffset;

        #         const scrollInterval = setInterval(function() {
        #             // Check if we have reached the bottom of the page
        #             if (currentScrollPosition >= totalPageHeight - viewportHeight) {
        #             clearInterval(scrollInterval); // Stop the scrolling
        #             console.log("Reached the bottom of the page.");
        #             return;
        #             }

        #             // Scroll down by the defined step amount
        #             window.scrollBy(0, scrollStep);
        #             currentScrollPosition += scrollStep;
        #         }, scrollIntervalTime);
        #         }
        #  simulateStepByStepScroll();
        # """

        # sb.execute_script(multi_line_script)
        #OnboardingSheetLottie_OnboardingSheetInternationalButton__CUHff
        #sb.wait_for_element_present("button.OnboardingSheetLottie_OnboardingSheetInternationalButton__CUHff", timeout=10)
        #sb.assert_element('button[class*="OnboardingSheetLottie_OnboardingSheetInternationalButton__CUHff"]')

        #sb.click("button.OnboardingSheetLottie_OnboardingSheetInternationalButton__CUHff")
        #sb.click('body')
        #sb.get_page_source()
        sb.sleep(2)
        for i in range(0, 8000,1000):
            sb.execute_script(f"document.querySelector('.bg-neutral-60.h-screen.overflow-y-auto').scrollTo(0, {i});")
            sb.save_screenshot('./ss/mmt_res.png')
            sr = sb.get_page_source()
            #sr = sb.get_attribute(".listingContainer div","innerHTML")
            write_to_file(sr,filename=f"./scrapper/ss/mmt_res_{i}.html",mode="w")
            
        print("Scraping completed")
        sb.quit()

def write_to_file(content, filename="./scrapper/mmt_res.html",mode="a"):
    with open(filename, mode, encoding="utf-8") as f:
            f.write(content)


if __name__ == "__main__":
    scrap_sb()
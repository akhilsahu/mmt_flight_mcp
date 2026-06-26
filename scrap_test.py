import sys
import os

# 1. Ensure the current directory is in the path so 'scrapper' is found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # 2. Import the specific module using the package dot notation
    from scrapper.paytm import scrap_extract
    
    def run_scraper():
        print("--- Starting   Scraper Execution ---")
        
        # 3. Call the execute function defined in your scrap_extract.py
        
        v = scrap_extract.execute("LKO", "DEL", "30/03/2026") 
        print(f"--- Execution Completed Successfully ---: {v}")
            
       
         

except ImportError as e:
    print(f"Import Error: {e}")
    print("Tip: Ensure you have __init__.py files in your 'scrapper' and 'cleartrip' folders.")

if __name__ == "__main__":
    run_scraper()
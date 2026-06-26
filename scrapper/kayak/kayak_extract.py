import requests
import json

# --- CONFIGURATION: Update these when cookies/headers expire ---
# Simply paste the new values here tomorrow.
COOKIES = (
    'Apache=JAUCAWAJgRHQOovP$59kzQ-AAABmJzuk_8-57-a38SzA; kayak=3ixzT7vuolARwaceRVac; kmkid=Abt2GyaZPq5PmjmI8yzXBh4; _fbp=fb.1.1754979562000.0.41689534847757315; _ga=GA1.1.1283338358.1754979563; kanid=; kanlabel=; csid=add2ed4e-a6ad-4ac2-b1a8-26ac9884fc3d; _gcl_au=1.1.40899675.1774209618; _gcl_aw=GCL.1774209619.Cj0KCQjwpv7NBhCzARIsADkIfWxSabV20Ksje4pUPXU6WHsyzVjhsKpdKVmxergSpyOFCXeIdmojC2EaAjq1EALw_wcB; _yoid=1c6a5fc3-b6fe-4d7d-ad4f-a9d690228b6d; _yosid=cc14b5e4-4258-4169-b0f1-c57236385641; g_state={"i_l":0,"i_ll":1774551229265,"i_b":"mVN5ary+8nEq7tTA64ZNGrIvXzOhc+V7NhoCVLqv+9A","i_e":{"enable_itp_optimization":0}}; cluster=4; p1.med.sid=R-4HweG5EPw8OjKbFAYoBnn-0odiblTfEPRzi98ITvvGO79f3XOic8u5ONnsI7h_R; __gads=ID=c740a2ec5b8f58c3:T=1754979563:RT=1774629737:S=ALNI_MaKWwMkP9Q2bS7WcPSODW-1Assccg; __gpi=UID=0000117ecf343f0d:T=1754979563:RT=1774629737:S=ALNI_MYVgnNRxQldzRAtKvr68gluBlcAPQ; __eoi=ID=3a657e65f5f175c9:T=1774209619:RT=1774629737:S=AA-AfjZBNIpm2-fJFGV3ovJkm0Sw; FCCDCF=%5Bnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%5B%5B32%2C%22%5B%5C%224d92f734-53bb-4166-9818-0cf1209af706%5C%22%2C%5B1774209619%2C531000000%5D%5D%22%5D%5D%5D; _ga_PWCRSK2Y5Y=GS2.1.s1774628227$o5$g1$t1774629748$j59$l0$h1452230005; FPGSID=1.1774628227.1774629748.G-PWCRSK2Y5Y.r0vm_FiTU5vYVcBCIFsNuw; forterToken=544199c5c63e4366b451627fd2400a10_1774629745894__UDF43-m4_21ck_; FCNEC=%5B%5B%22AKsRol-O_wnrXkrVX6nXjsansNW6YLWljQHx_Kk5f8sga7_nYIVbAC3-OTE2lJ46OXFNAyxf5x_VSHWZe1X1ql2urtDKmhQnoEUjtRAoDCHK500RfFm8hppyuEN3k90ejfyO9nd2ZTkhMJAs3ewd_NmcFfCBcOpvKg%3D%3D%22%5D%5D; hiddenParamsDEL-LKO%2F2026-05-27%3Fucs%3Dwbpr74=id=1774629761&page_origin=&src=&searchingagain=&c2s=&po=&personality=&provider=-1&pageType=RP; _uetsid=21b390f0294511f1a198b712a2301a39|l2cdso|2|g4p|0|2276; _uetvid=4a827880774411f0bd034b1a3b135fe4|1l4xi7k|1774629748934|2|1|bat.bing.com/p/insights/c/z; kayak.mc=AV0j17W2BKwlWNMw4Am5kIoGb4drgdUKtMoGw8a0kZTn3U52wZ3VwZHZ7midvb_e18WDCvo3XHqVL7PgiX7_XNCNun-OrG-2kDJTgCmmo_Hk-O7y1SPzAl7Y1JZyj9GxUMLCRKrlhdJhb4DRAhZM-_PWkuLTZjGecrF-6EYYChlKKD6CSOS6dSD91Kw4dvhPXTJcQUVuuY0cfXalK6pi_Ka5ntKepHb4fwctVAUZfrjFl9y18Hczu9Mz3dCB3jGzUlPOyLmxrWGbhTeynw1-6i_J-1y8_Q3S8pcHnv1NTzY9ViXoNto6R4buv_SHyPN-1y_sOssPF74Zm3SDUBz5rtwp1nN2GXe1BdnEeZbjD1M-9gi4dZ9tChKyZtqX3FG7umn8SSQ7tilupZO5cqwwMY6y6vEy6COxIhjrmO3zuXBRqzFABtSpJnNmqW3T2p-v1rIppD8IIv0jngK32snOLcoE11in4HdmKv6NEwfDvxpyC2N0zLo34Q9IgWwCaR9ZEyrUmD7kPlHPV4D0FcHT5D-63DHQWgmN93PZhC1L5VX3ZSkTcMSaWd1VmsLYC6MFu-ScIu7kIkleTBGDMcbmt_jZY3_fvWiUEsuB5l4NeVJ8hxuAAbkNSfooPqjFSlLsD-N6eDAS_krypMwtMQHA1mbZzSNP5Wijtv4ugt3E_GKWZcn_qpydPryFZH33xUJPvO_1G6TkWx_tZvWbFDRAFxQ4ABzm3c7LMMS7QmeMuP8dpFnvm0omB_UNTuqRbxpJiRAWk9GDAzRnVTy0lRsUJL9iEvf3h49NyidzhR0DGVj-79KicjJxDfkvGRAhSVj81RLto5Y-C_3sMsKyKyt_HzDPv8SFTVAejzAuO-MPlYH7CTgWP4TawXcEHN7eO6TTU6WxhQJ9ev7YLrWu-Mpyrci15DNT5qC-7vgGsN2Ic-O034itVtENlxOtUOlWrNbZMA; mst_iBfK2g=nvj8ROFxwPO2OTSVdmv7uUl0ArVjoyDjfsAEUqJavIxZCbVPth4Z4N9yWa2-epebDe_CpJqtXBzzrSg2nNNsuzxnSlZb__z4nHQkGyVyk-I; mst_ADIrkw=TNxrGHr768ox3sMo3-JQqJ-r1WYLOJpsYKn4CujlkPxZCbVPth4Z4N9yWa2-epebbLq6fRjgCq-4-mTs9i1ZxLwtVc7cQPIDmt-fRKSYBtc'
 
)

CSRF_TOKEN = 'YyrztOjM7S2woUiZodVV3Vk0vxh4m_8WDM7QR49eL$4-hEgNUcnJ1LtJSNXsqDHOxqHC0aT1sYHGtA9hcShzDKA'
# -------------------------------------------------------------

def poll_kayak_data(search_id, origin="DEL", destination="LKO", travel_date="2026-04-28", ucs="a3ovn8"):
    """
    Polls the Kayak API for flight results using a pre-existing search_id.
    """
    url = 'https://www.kayak.co.in/i/api/search/dynamic/flights/poll'
    
    # Constructing dynamic referer
    referer = f"https://www.kayak.co.in/flights/{origin}-{destination}/{travel_date}?fs=fdDir%3Dfalse&ucs={ucs}"

    headers = {
        'accept': '*/*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/json',
        'cookie': COOKIES,
        'origin': 'https://www.kayak.co.in',
        'priority': 'u=1, i',
        'referer': referer,
        'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
        'x-csrf': CSRF_TOKEN,
        'x-requested-with': 'XMLHttpRequest',
    }

    payload = {
        "filterParams": {"fs": "fdDir=false"},
        "userSearchParams": {
            "legs": [
                {
                    "origin": {"airports": [origin], "locationType": "airports"},
                    "destination": {"airports": [destination], "locationType": "airports"},
                    "date": travel_date,
                    "flex": "exact"
                }
            ],
            "searchId": search_id,  # Injected the search_id here
            "pageType": "results",
            "passengers": ["ADT"],
            "passengerDetails": [{"ptc": "ADT"}]
        },
        "searchMetaData": {
            "pageNumber": 1, 
            "searchTypes": [], 
            "skipResultsInSecondPhase": False
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 401:
            print("❌ 401 Unauthorized: Update RAW_COOKIES and CSRF_TOKEN.")
            return None
            
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Polling failed: {e}")
        return None

def scrap_data(origin="DEL", destination="LKO", travel_date="2026-04-28", ucs="a3ovn8"):
    """
    Initiates a flight search poll to retrieve a searchId and initial flight data.
    """
    url = 'https://www.kayak.co.in/i/api/search/dynamic/flights/poll'
    
    # Dynamic referer based on your parameters
    referer = f"https://www.kayak.co.in/flights/{origin}-{destination}/{travel_date}?fs=fdDir%3Dfalse&ucs={ucs}"

    headers = {
        'accept': '*/*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/json',
        'cookie': COOKIES,
        'origin': 'https://www.kayak.co.in',
        'priority': 'u=1, i',
        'referer': referer,
        'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
        'x-csrf': CSRF_TOKEN,
        'x-requested-with': 'XMLHttpRequest',
    }

    # Payload structured exactly as per your CURL to trigger a searchId generation
    payload = {
        "filterParams": {
            "fs": "fdDir=false"
        },
        "userSearchParams": {
            "legs": [
                {
                    "origin": {"airports": [origin], "locationType": "airports"},
                    "destination": {"airports": [destination], "locationType": "airports"},
                    "date": travel_date,
                    "flex": "exact"
                }
            ],
            "pageType": "results",
            "passengers": ["ADT"],
            "passengerDetails": [{"ptc": "ADT"}]
        },
        "searchMetaData": {
            "pageNumber": 1,
            "searchTypes": []
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        res = response.json() 
        search_id = res.get('searchId')
        search = poll_kayak_data(search_id,origin,destination,travel_date)
        if response.status_code == 401:
            print("❌ 401 Unauthorized: Update your Cookies and CSRF token in the config section.")
            return None
            
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

# --- EXECUTION ---
if __name__ == "__main__":
    result = scrap_data()
    
    if result:
        # Looking for the searchId in the response
        search_id = result.get('searchId') or result.get('userSearchParams', {}).get('searchId')
        
        if search_id:
            print(f"✅ Successfully retrieved Search ID: {search_id}")
        else:
            print("✅ Request successful, but no explicit Search ID found in the top level of JSON.")
            # You might want to print result.keys() here to see where the ID is hidden
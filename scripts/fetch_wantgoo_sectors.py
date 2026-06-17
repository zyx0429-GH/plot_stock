import requests
from bs4 import BeautifulSoup
import time
import json

stocks = [
    "1216","1301","1319","1590","1605","1727","1815","2002","2023","2025",
    "2030","2031","2032","2033","2034","2301","2303","2308","2313","2317",
    "2324","2327","2330","2337","2344","2345","2352","2355","2356","2357",
    "2368","2375","2376","2377","2382","2383","2404","2408","2409","2428",
    "2439","2449","2454","2481","2492","2634","2850","2880","2881","2882",
    "2883","2885","2886","2887","2890","2892","3005","3006","3008","3016",
    "3017","3026","3036","3037","3045","3090","3217","3231","3236","3264",
    "3274","3356","3357","3376","3443","3450","3481","3498","3535","3537",
    "3624","3653","3661","3663","3665","3675","3680","3707","3709","3711",
    "4919","4961","4966","4967","5274","5291","5328","5347","5425","5439",
    "6104","6127","6147","6173","6182","6187","6191","6207","6213","6223",
    "6239","6257","6261","6271","6274","6284","6415","6462","6485","6510",
    "6515","6669","6727","6770","6805","6821","8040","8042","8043","8046",
    "8091","8096","8150","8210","8261","8289","8358","8996","00981A"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
}

results = {}

for sid in stocks:
    url = f"https://www.wantgoo.com/stock/{sid}"
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        # Force UTF-8 decoding
        text = r.content.decode('utf-8', errors='replace')
        soup = BeautifulSoup(text, "html.parser")
        
        industry = "未知"
        # Look for industry link
        for a in soup.find_all("a"):
            href = a.get("href", "")
            if "/index/listed/industry" in href or "/index/^" in href:
                txt = a.get_text(strip=True)
                # Exclude "上市" itself
                if txt and txt != "上市" and len(txt) > 1:
                    industry = txt
                    break
        
        # Fallback: look in breadcrumb list
        if industry == "未知":
            for li in soup.find_all("li"):
                a = li.find("a")
                if a and "/index/" in a.get("href", ""):
                    txt = a.get_text(strip=True)
                    if txt and txt not in ["上市", "台股", "首頁"] and len(txt) > 1:
                        industry = txt
                        break
        
        results[sid] = industry
        # Use ascii-safe print
        safe = industry.encode('ascii', 'replace').decode('ascii')
        print(f"{sid}: {safe}")
    except Exception as e:
        results[sid] = f"ERROR"
        print(f"{sid}: ERROR")
    time.sleep(0.3)

with open("wantgoo_sectors.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\nDone!")

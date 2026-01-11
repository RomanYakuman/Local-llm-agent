import trafilatura
import requests
import re
import random
import time
from ddgs import DDGS

def clean_trafilatura_xml(xml_text):
    if not xml_text: return ""   
    # <list rend="ul"> -> <list>
    xml_text = re.sub(r' (\w+)="[^"]+"', '', xml_text)
    # <lb/> -> \n
    xml_text = xml_text.replace("<lb/>", "\n")
    # Tag shortening
    # <item> -> <li>
    xml_text = xml_text.replace("<item>", "<li>").replace("</item>", "</li>")
    # <list> -> <ul>
    xml_text = xml_text.replace("<list>", "<ul>").replace("</list>", "</ul>")
    return xml_text

def ddgs_search(query:str):
    full_text = ''
    try:
        results = list(DDGS().text(query, max_results=4, safesearch='off', region='wt-wt'))
    except Exception as e:
        return f"System Log: Search engine connection failed: {e}"

    if not results:
        return "System Log: Search returned 0 results. Try a different query."
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "Accept-Encoding": "gzip, deflate"
    }
    print(f'\n\naction input: {query}\n\n')
    for result in results:
        url = result['href']
        if not url: continue
        try:
            time.sleep(random.uniform(0.5, 1.5))
            response = requests.get(url, headers=HEADERS, timeout=8, verify=False)
            if response.status_code == 200:
                #getting text from url with xml tags for better readability for the model
                extracted_text = trafilatura.extract(response.text, output_format='xml', include_tables=True)
                extracted_text = clean_trafilatura_xml(extracted_text)
                MAX_CHARS = 4000
                if len(extracted_text) > MAX_CHARS:
                    extracted_text=extracted_text[:MAX_CHARS]+f'\n... [Truncated. Only first {MAX_CHARS} chars shown]'
                    
                full_text += f'<web_page url="{url}">\n{extracted_text}\n</web_page>\n\n'

        except Exception as e:
            full_text +=  f'<web_page url="{url}">\nText extraction failed\n</web_page>\n\n'
            print(f'Extraction error: {e}')
    return full_text


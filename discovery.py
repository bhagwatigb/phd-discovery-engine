# discovery.py
import json
import time
from ddgs import DDGS

CORE_DOMAINS = [
    "computational biology",
    "bioinformatics",
    "systems biology",
    "metabolic modelling",
    "systems medicine"
]

def find_candidate_urls(university: dict) -> list[str]:
    domain = university.get("domain", "").strip()
    
    if not domain or "wikipedia" in domain or domain.endswith(".com"):
        if not any(domain.endswith(tld) for tld in [".edu", ".ac.uk", ".ch", ".de", ".se", ".dk", ".nl", ".br", ".mx", ".ca"]):
            return []

    domain_query = " OR ".join([f'"{d}"' for d in CORE_DOMAINS])
    # Exclude PDFs directly in the search engine query
    query = f'site:{domain} ("PhD" OR "Doctoral") ({domain_query}) ("apply" OR "deadline") -filetype:pdf'
    
    candidate_urls = []
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=4)
            for res in results:
                url = res.get("href", "")
                
                # Double-check Python-side to block documents and ensure it's the right domain
                if domain in url and not url.lower().endswith(('.pdf', '.doc', '.docx', '.ppt')):
                    candidate_urls.append(url)
        time.sleep(1.2)
    except Exception as e:
        print(f"Discovery lookup failed for {domain}: {e}")
        
    return candidate_urls

def run_discovery() -> list[dict]:
    with open("universities_seed.json", "r") as f:
        universities = json.load(f)
        
    discovery_queue = []
    for uni in universities:
        urls = find_candidate_urls(uni)
        for url in urls:
            discovery_queue.append({
                "university": uni["name"],
                "region": uni.get("region", "Unknown"),
                "url": url
            })
    return discovery_queue

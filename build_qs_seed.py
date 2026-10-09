# build_qs_seed.py
import json
import re
import asyncio
import requests
from playwright.async_api import async_playwright
from rapidfuzz import process, fuzz

# Target Subject URLs
SUBJECT_URLS = [
    "https://www.topuniversities.com/university-subject-rankings/life-sciences-medicine",
    "https://www.topuniversities.com/university-subject-rankings/biological-sciences"
]

# Exact regions to select in the filter modal
TARGET_REGIONS = ["North America", "Europe", "Latin America"]
TARGET_COUNT = 50

DOMAINS_URL = "https://raw.githubusercontent.com/Hipo/university-domains-list/master/world_universities_and_domains.json"

def load_domain_lookup():
    print("Fetching global university domain registry...")
    try:
        r = requests.get(DOMAINS_URL, timeout=15)
        records = r.json()
        lookup = {}
        for item in records:
            name = item.get("name", "").strip()
            domains = item.get("domains", [])
            if name and domains:
                lookup[name] = domains[0].lower().replace("www.", "")
        return lookup
    except Exception as e:
        print(f"Warning: Failed to fetch online domain registry: {e}")
        return {}

def resolve_domain(uni_name: str, domain_lookup: dict) -> str:
    if not domain_lookup:
        slug = re.sub(r"[^a-zA-Z0-9]", "", uni_name).lower()
        return f"{slug}.edu"
        
    if uni_name in domain_lookup:
        return domain_lookup[uni_name]
    
    clean_name = re.sub(r"\(.*?\)", "", uni_name).strip()
    if clean_name in domain_lookup:
        return domain_lookup[clean_name]

    names = list(domain_lookup.keys())
    match, score, _ = process.extractOne(clean_name, names, scorer=fuzz.token_sort_ratio)
    if score >= 75:
        return domain_lookup[match]

    slug = re.sub(r"[^a-zA-Z0-9]", "", clean_name).lower()
    return f"{slug}.edu"

async def extract_for_subject_and_region(page, subject_url, region_name, domain_lookup):
    print(f"\n--- Loading: {subject_url.split('/')[-1]} | Region: {region_name} ---")
    await page.goto(subject_url, wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(5000)

    # Handle cookie popup if present
    try:
        cookie_btn = page.locator("#onetrust-accept-btn-handler")
        if await cookie_btn.is_visible(timeout=2000):
            await cookie_btn.click()
            await page.wait_for_timeout(2000)
    except Exception:
        pass

    # Open "Apply Filters" modal and select region using pure JS evaluation to bypass visibility blocks
    try:
        await page.evaluate('''() => {
            const btns = Array.from(document.querySelectorAll('button, div'));
            const filterBtn = btns.find(b => b.innerText && b.innerText.includes('Apply Filters'));
            if (filterBtn) filterBtn.click();
        }''')
        await page.wait_for_timeout(2000)
        
        # Click the Region dropdown
        await page.evaluate('''() => {
            const labels = Array.from(document.querySelectorAll('label, div, span, h3'));
            const regionLabel = labels.find(el => el.innerText && el.innerText.trim() === 'Region');
            if (regionLabel) {
                const container = regionLabel.parentElement || regionLabel.parentElement.parentElement;
                // Target the React select control area or any clickable input
                const dropdown = container.querySelector('.select__control, [class*="control"], input, [role="combobox"]');
                if (dropdown) dropdown.click();
            }
        }''')
        await page.wait_for_timeout(1500)
        
        # Click the actual region text option
        await page.evaluate(f'''(region_name) => {{
            const options = Array.from(document.querySelectorAll('.select__option, [role="option"], li, div'));
            const option = options.find(o => o.innerText && o.innerText.trim() === region_name);
            if (option) option.click();
        }}''', region_name)
        await page.wait_for_timeout(1500)
        
        # Click "Show results" or "Apply"
        await page.evaluate('''() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const submitBtn = btns.find(b => b.innerText && (b.innerText.includes('Show results') || b.innerText.includes('Apply')));
            if (submitBtn) submitBtn.click();
        }''')
        await page.wait_for_timeout(6000)
        
    except Exception as e:
        print(f"UI Filter automation error for {region_name}: {e}")

    # Scroll down to lazily load the rows
    for _ in range(8):
        await page.mouse.wheel(0, 1500)
        await page.wait_for_timeout(1000)

    # Extract up to the Top 50 names
    extracted = await page.evaluate('''() => {
        const results = [];
        const links = Array.from(document.querySelectorAll('a[href*="/universities/"]'));
        const seen = new Set();
        
        for (const a of links) {
            const name = a.innerText ? a.innerText.trim() : "";
            if (!name || seen.has(name) || name.length < 3 || name.includes("\\n")) continue;
            seen.add(name);
            results.push(name);
        }
        return results;
    }''')

    records = []
    for rank_idx, uni_name in enumerate(extracted[:TARGET_COUNT], start=1):
        domain = resolve_domain(uni_name, domain_lookup)
        records.append({
            "name": uni_name,
            "regional_rank": rank_idx,
            "region": region_name,
            "domain": domain
        })

    print(f"Extracted {len(records)} universities.")
    return records

async def main():
    domain_lookup = load_domain_lookup()
    master_dict = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for subject_url in SUBJECT_URLS:
            for region in TARGET_REGIONS:
                records = await extract_for_subject_and_region(page, subject_url, region, domain_lookup)
                
                # Deduplicate institutions that appear in both Biological Sciences and Life Sciences
                for rec in records:
                    if rec["name"] not in master_dict:
                        master_dict[rec["name"]] = rec
        
        await browser.close()

    final_seed = list(master_dict.values())
    with open("universities_seed.json", "w") as f:
        json.dump(final_seed, f, indent=2)

    print(f"\nDone! Saved {len(final_seed)} unique institutions to universities_seed.json.")

if __name__ == "__main__":
    asyncio.run(main())

# extractor.py
import json
from typing import Optional, Literal
from pydantic import BaseModel, Field
import ollama
from crawl4ai import AsyncWebCrawler

class PhDPositionSchema(BaseModel):
    is_valid_open_position: bool = Field(description="False if this is an expired post, syllabus, general lab page, or faculty profile with no open roles.")
    department_or_lab: Optional[str] = None
    position_title: Optional[str] = None
    matched_domains: list[str] = Field(default_factory=list, description="e.g. Computational Biology, Metabolic Modelling")
    application_mode: Literal["portal_based", "pi_contact", "hybrid", "unknown"] = "unknown"
    pi_name: Optional[str] = None
    pi_email: Optional[str] = None
    portal_opening_date: Optional[str] = None
    application_deadline: Optional[str] = None
    min_cgpa_or_grade: Optional[str] = None
    degree_required: Optional[str] = None
    language_requirements: Optional[str] = None
    application_link: Optional[str] = None

async def extract_phd_data(url: str, university: str) -> Optional[dict]:
    content_markdown = ""
    
    try:
        # Wrap crawler in exception handler to prevent total crashes
        async with AsyncWebCrawler(verbose=False) as crawler:
            # magic=True enables anti-bot evasion for 403 Forbidden pages
            result = await crawler.arun(
                url=url,
                magic=True,
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            
            if not result.success:
                print(f"Scrape blocked or failed for {url}")
                return None
                
            content_markdown = result.markdown[:7000]
    except Exception as e:
        print(f"Crawler crashed on {url}: {e}")
        return None

    if not content_markdown:
        return None

    system_prompt = (
        "You are an academic recruitment extraction engine. Analyze web page content "
        "and determine if it contains an active, open PhD position in: "
        "Life Sciences, Computational Biology, Bioinformatics, Systems Biology, Metabolic Modelling, or Systems Medicine. "
        "If it is not an active open position, set is_valid_open_position to false."
    )

    user_prompt = f"University: {university}\nURL: {url}\nPage Content:\n{content_markdown}"

    try:
        response = ollama.chat(
            model="llama3.2:3b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            format=PhDPositionSchema.model_json_schema(),
            options={"temperature": 0.0}
        )

        raw_json = json.loads(response["message"]["content"])
        validated_obj = PhDPositionSchema(**raw_json)

        if validated_obj.is_valid_open_position:
            return validated_obj.model_dump()
        return None
    except Exception as e:
        print(f"Ollama extraction failed on {url}: {e}")
        return None

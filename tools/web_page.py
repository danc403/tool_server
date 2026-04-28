# web_page.py
import json
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

async def fetch_and_parse_url(url: str) -> dict:
    """
    Fetches the content of a given web page URL, extracts its plain text,
    and lists all accessible links found within the page.

    This tool is useful for getting the raw content of a webpage for summarization,
    specific information extraction, or for the LLM to follow navigation paths.

    Args:
        url (str): The full URL of the web page to retrieve.
                   Example: "https://en.wikipedia.org/wiki/Artificial_intelligence"

    Returns:
        dict: A dictionary representing the JSON response.
              The structure will always contain a 'status' key.

              On **success**, the JSON will have the following structure:
              ```json
              {
                "status": "success",
                "data": {
                  "url": "original_url_requested",
                  "plain_text_content": "Extracted plain text from the webpage...",
                  "extracted_links": [
                    "[https://example.com/link1](https://example.com/link1)",
                    "[https://example.com/link2](https://example.com/link2)"
                  ]
                }
              }
              ```
              `plain_text_content` will contain the main readable text of the page.
              `extracted_links` will be a list of absolute URLs found in 'href' attributes.

              On **failure** (e.g., invalid URL, network error, page not found,
              or content parsing issues), the JSON will have the following structure:
              ```json
              {
                "status": "error",
                "message": "A descriptive error message indicating what went wrong."
              }
              ```
    """
    try:
        if not isinstance(url, str) or not url.strip():
            return {"status": "error", "message": "URL cannot be empty."}

        # Basic URL validation
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            return {"status": "error", "message": f"Invalid URL format: '{url}'. Please provide a complete URL (e.g., https://example.com)."}

        # Using aiohttp as it is the async standard in the current environment
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    return {"status": "error", "message": f"HTTP error {response.status} while fetching '{url}'"}
                
                html_content = await response.text()

        # Using lxml for high-performance parsing within the tool server
        soup = BeautifulSoup(html_content, 'lxml')

        # Extract plain text content
        # Remove script and style tags to get cleaner text
        for script_or_style in soup(['script', 'style', 'header', 'footer', 'nav']):
            script_or_style.extract()
            
        plain_text_content = soup.get_text(separator='\n', strip=True)

        # Extract links
        extracted_links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            # Convert relative URLs to absolute URLs
            absolute_url = urljoin(url, href)
            # Basic check to ensure it's a valid looking HTTP/HTTPS link
            if urlparse(absolute_url).scheme in ['http', 'https']:
                extracted_links.append(absolute_url)

        # Remove duplicates and cap to protect LLM context window
        extracted_links = list(set(extracted_links))[:50]

        return {
            "status": "success",
            "data": {
                "url": url,
                "plain_text_content": plain_text_content[:10000], # Cap text to 10k chars
                "extracted_links": extracted_links
            }
        }

    except aiohttp.ClientError as e:
        return {"status": "error", "message": f"Network or request error while fetching '{url}': {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred while processing '{url}': {str(e)}"}

async def web_page(url: str) -> str:
    """
    Fetches the content of a web page and extracts readable text and links.

    Args:
        url (str): The URL of the page to scrape.

    Returns:
        str: A JSON string containing extracted text and links or an error message.
    """
    result = await fetch_and_parse_url(url)
    return json.dumps(result, indent=2)

# web_search.py
import json
import asyncio
from duckduckgo_search import DDGS # Using standard version with thread offloading

async def web_search(
    query: str,
    search_engine: str = "duckduckgo", # Defaulting to DuckDuckGo, using direct integration
) -> dict:
    """
    Performs a web search for the given query and returns the top 5 results,
    including their titles (blurbs) and URLs, leveraging a specified search engine.

    By default, this tool uses DuckDuckGo by directly querying its public search
    interface, similar to how command-line tools like 'ddgr' operate. This method
    does not require an API key for basic web search results.

    Args:
        query (str): The search query string.
                     Example: "how to compile rust on linux"
        search_engine (str, optional): The name of the search engine to use.
                                       Defaults to "duckduckgo". If a different
                                       engine is specified (e.g., "google_cse" requiring
                                       an actual API integration), your server-side
                                       implementation would handle that.

    Returns:
        dict: A dictionary representing the JSON response.
              The structure will always contain a 'status' key.

              On **success**, the JSON will have the following structure:
              ```json
              {
                "status": "success",
                "data": {
                  "query": "original search query",
                  "search_engine_used": "engine_name",
                  "results": [
                    {
                      "title": "Title of the first search result",
                      "snippet": "A brief summary or blurb of the first result.",
                      "url": "[https://example.com/first-result-link](https://example.com/first-result-link)"
                    },
                    {
                      "title": "Title of the second search result",
                      "snippet": "A brief summary or blurb of the second result.",
                      "url": "[https://example.com/second-result-link](https://example.com/second-result-link)"
                    }
                    // ... up to 5 results
                  ]
                }
              }
              ```
              The `results` array will contain up to 5 objects, each with 'title', 'snippet', and 'url'.

              On **failure** (e.g., network error, DuckDuckGo's public interface changes,
              or a different unsupported search engine is specified),
              the JSON will have the following structure:
              ```json
              {
                "status": "error",
                "message": "A descriptive error message indicating what went wrong."
              }
              ```
    """
    try:
        if not isinstance(query, str) or not query.strip():
            return {"status": "error", "message": "Search query cannot be empty."}

        # --- Actual DuckDuckGo Integration using synchronous DDGS offloaded to a thread ---
        if search_engine.lower() == "duckduckgo":
            
            def perform_search():
                with DDGS() as ddgs:
                    # DDGS text returns a generator; we convert to list immediately
                    return list(ddgs.text(keywords=query, max_results=5))

            # Run the blocking DDGS call in a separate thread to keep the event loop free
            raw_results = await asyncio.to_thread(perform_search)

            formatted_results = []
            for item in raw_results:
                formatted_results.append({
                    "title": item.get('title', 'No Title'),
                    "snippet": item.get('body', 'No snippet available.'), # DDGS text search uses 'body' for snippet
                    "url": item.get('href', '#')
                })

            return {
                "status": "success",
                "data": {
                    "query": query,
                    "search_engine_used": search_engine,
                    "results": formatted_results
                }
            }
        else:
            # Handle other search engines if you decide to add them later
            return {"status": "error", "message": f"Unsupported search engine: '{search_engine}'. Currently only 'duckduckgo' is supported without an API key."}

    except Exception as e:
        # Catch any errors from DDGS or other unexpected issues
        return {
            "status": "error",
            "message": f"An error occurred during web search for '{query}': {str(e)}. DuckDuckGo's public interface may have changed, or there's a network issue."
        }

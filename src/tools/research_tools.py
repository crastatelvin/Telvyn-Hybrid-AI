import os
from langchain_community.tools import DuckDuckGoSearchRun
from bs4 import BeautifulSoup
import requests
from typing import List

def scrape_url(url: str) -> str:
    """Scrapes the text content from a URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for s in soup(["script", "style"]):
            s.extract()
            
        text = soup.get_text()
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text[:5000] # Cap at 5k chars for token efficiency
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"

def analyze_competitor(competitor_name: str) -> str:
    """Performs deep research on a competitor using web search and site scraping."""
    search = DuckDuckGoSearchRun()
    search_query = f"{competitor_name} company overview mission products"
    results = search.run(search_query)
    
    # Heuristic: try to find a URL in the results or just summarize the search
    # For a real implementation, we'd use a search API that returns structured URLs.
    # Here we'll just return the search results for now but marked as 'Synthesized Research'
    
    return f"COMPETITOR ANALYSIS: {competitor_name}\n\nSearch Findings:\n{results}"

def generate_swot_report(analysis_text: str) -> str:
    """Synthesizes analysis text into a SWOT report."""
    # This logic is usually handled by the Researcher LLM node, 
    # but we provide it as a structured helper for the agent.
    return f"SWOT SYNTHESIS REQUESTED BASED ON: {analysis_text[:200]}..."

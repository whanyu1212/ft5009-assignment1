import os
import json
from google import genai
from typing import List, Optional
from google.genai import types
from firecrawl import Firecrawl
from dotenv import load_dotenv

# from config import IndividualStock, SP500Constituents

load_dotenv()

# Global client instance for reuse
_genai_client: Optional[genai.Client] = None


def get_genai_client() -> genai.Client:
    """Get or create a singleton Gemini AI client instance."""
    global _genai_client
    if _genai_client is None:
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        _genai_client = genai.Client(api_key=gemini_api_key)
    return _genai_client


# REFERENCE: https://docs.firecrawl.dev/sdks/python
def scrape_static_website(url: str, format: List[str] = ["markdown"]) -> str:
    """Scrape a static website and return the content in the specified format
    using firecrawl API

    Args:
        url (str): The URL of the website to scrape.
        format (List[str], optional): The format(s) to return the content in.
        Defaults to ["markdown"].

    Returns:
        str: The scraped content in the specified format.

    Raises:
        ValueError: If API key is not found or URL is invalid.
        Exception: If scraping fails due to network or API issues.
    """
    # Input validation
    if not url or not url.strip():
        raise ValueError("URL cannot be empty or None")

    # Check if the API key exists
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError("FIRECRAWL_API_KEY environment variable is not set")

    try:
        firecrawl = Firecrawl(api_key)
        scraped_content = firecrawl.scrape(url, formats=format)

        # Check if scraping was successful
        if not scraped_content:
            raise Exception(f"Empty response scraped from {url}")

        # Dynamically return content based on the first format specified
        primary_format = format[0] if format else "markdown"

        # Get the content attribute dynamically
        if hasattr(scraped_content, primary_format):
            return getattr(scraped_content, primary_format)
        else:
            # Fallback to the entire response if the format attribute doesn't exist
            return str(scraped_content)

    except Exception as e:
        # Any other edge cases
        raise Exception(f"An error occurred while scraping: {str(e)}")


def llm_process_markdown(markdown_content: str, model: str = "gemini-2.5-flash") -> str:
    """Process markdown content using Gemini AI to extract S&P 500 data as JSON.

    Args:
        markdown_content (str): The markdown content to process
        model (str, optional): The Gemini model to use.
        Defaults to "gemini-2.5-flash".

    Raises:
        ValueError: If markdown_content is empty or None
        Exception: If LLM processing fails

    Returns:
        str: JSON formatted S&P 500 company data
    """
    if not markdown_content or not markdown_content.strip():
        raise ValueError("Markdown content cannot be empty")

    try:
        client = get_genai_client()
        response = client.models.generate_content(
            model=model,
            contents=types.Part.from_text(
                text="""Please help to format the unstructured data into the designated JSON format. 
                Only include the S&P 500 component stocks table and omit any other information.
                The following is the unstructured data: \n\n"""
                + markdown_content
            ),
            config=types.GenerateContentConfig(
                system_instruction="You are a helpful assistant.",
                temperature=0.0,
                response_mime_type="application/json",
                # Enforcing output schema causes a serious performance bottleneck
                # Thus, it is currently disabled
                # response_schema=SP500Constituents,
            ),
        )
        return response.text
    except Exception as e:
        raise Exception(f"Failed to process markdown content with LLM: {str(e)}")


if __name__ == "__main__":
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    format = ["markdown"]
    scraped_content = scrape_static_website(url, format)
    print(type(scraped_content))
    processed_content = llm_process_markdown(scraped_content)
    print(processed_content)

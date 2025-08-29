import os
import json
import requests
import pandas as pd
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List, Optional, Union

from google import genai
from google.genai import types
from firecrawl import Firecrawl
from dotenv import load_dotenv

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


class TableScraper(ABC):
    """Abstract base class for table scrapers."""

    @abstractmethod
    def scrape_table(self, url: str) -> Union[str, pd.DataFrame]:
        """Scrape a table from a URL and return it either
        as a JSON string or a Pandas DataFrame."""
        pass


class LLMTableScraper(TableScraper):
    """Scrapes a table from a page and format it using LLM"""

    # TODO: add litellm adapter so the processing will be model agnostic

    @property
    def scraper_name(self) -> str:
        return "LLMTableScraper"

    def scrape_table(
        self, url: str, format: List[str] = ["markdown"]
    ) -> Union[str, pd.DataFrame]:
        """Scrape and process table from a URL using LLM.

        Args:
            url (str): The URL of the website to scrape.

        Returns:
            Union[str, pd.DataFrame]: The scraped table data as JSON or DataFrame.
        """
        markdown_content = self._scrape_static_website(url, format=format)
        processed_markdown_content = self._llm_process_markdown(markdown_content)

        df = pd.read_json(processed_markdown_content)
        return df

    def _scrape_static_website(self, url: str, format: List[str] = ["markdown"]) -> str:
        """Scrape a static website and return the content in the specified format.

        Args:
            url (str): The URL of the website to scrape.
            format (List[str], optional): The format to return the scraped content in.
            Defaults to ["markdown"].

        Raises:
            ValueError: If the URL is invalid.
            ValueError: If the format is unsupported.
            Exception: If an error occurs while scraping.
            Exception: If the scraped content is empty.

        Returns:
            str: The scraped content in the specified format.
        """

        if not url or not url.strip():
            raise ValueError("URL cannot be empty or None")

        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise ValueError("FIRECRAWL_API_KEY environment variable is not set")

        try:
            firecrawl = Firecrawl(api_key)
            scraped_content = firecrawl.scrape(url, formats=format)

            if not scraped_content:
                raise Exception(f"Empty response scraped from {url}")

            # * Does accommodate other formats such as html
            primary_format = format[0] if format else "markdown"
            if hasattr(scraped_content, primary_format):
                return getattr(scraped_content, primary_format)
            else:
                return str(scraped_content)
        except Exception as e:
            raise Exception(f"An error occurred while scraping: {str(e)}")

    def _llm_process_markdown(
        self,
        markdown_content: str,
        model: str = "gemini-2.5-flash",  # * simple reading and processing task, pro is an overkill
    ) -> Union[str, pd.DataFrame]:
        """Process markdown content using LLM to extract structured data.

        Args:
            markdown_content (str): The markdown content to process, extracted by _scrape_static_website.
            model (str, optional): The model to use for processing. Defaults to "gemini-2.5-flash".

        Raises:
            ValueError: If the markdown content is empty.
            Exception: If the LLM processing fails.

        Returns:
            Union[str, pd.DataFrame]: The processed table data as JSON or DataFrame.
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
                ),
            )
            return response.text
        except Exception as e:
            raise Exception(f"Failed to process markdown content with LLM: {str(e)}")


class PandasTableScraper(TableScraper):
    """Scrapes a table from a URL using pandas' read_html method."""

    @property
    def scraper_name(self) -> str:
        return "PandasTableScraper"

    def scrape_table(self, url: str, table_index: int = 0) -> str:
        """Scrape table from a URL using pandas and return it as a JSON string.

        Args:
            url (str): The URL of the website to scrape.

        Returns:
            str: JSON formatted table data.
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers)

            table = pd.read_html(response.text)
            # ! The first table is what we want from this static page
            df = table[0]
            return df
        except Exception as e:
            raise Exception(f"An error occurred while scraping with pandas: {str(e)}")


class ScraperType(Enum):
    """Enum for scraper types."""

    LLM = auto()
    PANDAS = auto()


class ScraperFactory:
    """Factory for creating table scrapers."""

    @staticmethod
    def get_scraper(scraper_type: ScraperType) -> TableScraper:
        """Get a scraper instance based on the specified type.

        Args:
            scraper_type (ScraperType): The type of scraper to create.

        Returns:
            TableScraper: An instance of the specified table scraper.

        Raises:
            ValueError: If an unknown scraper type is specified.
        """
        if scraper_type == ScraperType.LLM:
            return LLMTableScraper()
        elif scraper_type == ScraperType.PANDAS:
            return PandasTableScraper()
        else:
            raise ValueError(f"Unknown scraper type: {scraper_type}")

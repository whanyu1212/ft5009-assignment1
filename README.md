# FT5009 Assignment 1

### Objective
The goal of this assignment is to:
1. Apply Benford’s Law to the market capitalization data of S&P 500 constituent stocks. Please analyze whether the distribution of the first digits of the market capitalization data follows Benford’s Law and interpret their findings.
2. Find another financial metric for the S&P 500 constituent stocks and analyze whether the distribution of the first digits of the market capitalization data follows Benford’s Law and interpret their findings.

---
### Methodology and Analysis

#### Scraper for SP500 Constituents

Due to the absence of a free API for obtaining all the S&P 500 constituents, we resorted to scraping the data from Wikipedia. The implementation of the scraper can be found in [`src/data_loaders/wiki_sp500_scraper.py`](src/data_loaders/wiki_sp500_scraper.py).

Two methods were explored:

1.  **Firecrawl with Gemini**: This approach involved using Firecrawl (has a rate limit) to scrape the unstructured text from the Wikipedia page, followed by processing the text with the Gemini to extract the constituent data. However, the `litellm` adapter (making the processor model agnostic) for this process has not yet been implemented. Enforcing the response schema using Pydantic BaseModel also introduces a significant overhead. The schema can be found in [`src/utils/llm_response_schema.py`](src/utils/llm_response_schema.py).
   
2.  **Pandas `read_html`**: This method leverages the pandas library's `read_html` function to directly parse the HTML table from the Wikipedia page. This proved to be a much more performant and straightforward solution.

It is important to note that both approaches are ***not production-ready***. The data's **reliability is a concern**, as Wikipedia pages can be *edited by anyone at any time*, making the source data potentially **inconsistent**.

To address potential data quality issues, Pandera is integrated into the `scrap_table` method to perform automatic data validation immediately after scraping. The schema, defined in `SP500ConstituentSchema`, ensures that the scraped data conforms to the expected data types and constraints. The schema definition can be found in [`src/utils/schemas.py`](src/utils/schemas.py). 

#### Retrieving Stock info from YFinance

The `YFinanceLoader` class, found in [`src/data_loaders/yf_loader.py`](src/data_loaders/yf_loader.py), is responsible for fetching stock data from Yahoo Finance. It provides methods to retrieve general stock information and, more specifically, market capitalization data. The `get_stock_info` method can fetch multiple data fields for a list of tickers in a single call, which allows for thorough comparisons in subsequent analysis steps.

There are two implementations for fetching market capitalization, controlled by the `prefer_calc` parameter in the `get_market_cap` method:

1.  **Direct Fetching (`prefer_calc=False`)**: This is the default method. It retrieves the `marketCap` value directly from the stock's information. While this approach is faster as it requires fewer API calls, the data may not always be the most up-to-date.

2.  **Calculation (`prefer_calc=True`)**: This method calculates the market capitalization by multiplying the latest stock price (from `get_latest_ohlcv`) by the number of outstanding shares. This approach provides a more accurate, real-time market cap value but introduces performance overhead due to the additional API call required to fetch the latest price data.

The dual implementation offers a trade-off between performance and accuracy, allowing the user to choose the most suitable method for their needs.

Additionally, after fetching the data, it is validated against a Pandera schema defined in `MarketCapSchema` to ensure data integrity. The schema can be found in [`src/utils/schemas.py`](src/utils/schemas.py).

#### Benford's Law Analysis

The `BenfordsLawAnalyzer` class, located in [`src/analysis/benfords_law.py`](src/analysis/benfords_law.py), provides a comprehensive toolkit for testing conformity to Benford's Law.

The implementation is designed to be robust, incorporating multiple statistical tests to ensure a thorough analysis. While the core requirement of the assignment is the **Chi-Square test**, two additional tests have been included to complement the analysis and provide a more holistic view:

1.  **Chi-Square Goodness-of-Fit Test (Required)**: This test compares the observed frequency of first digits against the expected frequencies predicted by Benford's Law. It is the primary method used to determine if there is a statistically significant difference between the observed and theoretical distributions.

2.  **Kolmogorov-Smirnov (KS) Test (Supplemental)**: Unlike the Chi-Square test, which focuses on frequencies, the KS test compares the cumulative distribution functions (CDFs) of the observed and theoretical distributions. This provides a different perspective on conformity and is particularly sensitive to deviations in the overall shape of the distribution.

3.  **Mean Absolute Deviation (MAD) (Supplemental)**: MAD is a measure of the average deviation between the observed and expected proportions. It provides a straightforward metric of how closely the data fits the Benford's Law curve, with established thresholds for interpreting the degree of conformity (e.g., low, acceptable, marginal, or high dispersion).


Additionally, the analyzer includes the following features:
- **Automated Summary**: A summary interpretation is automatically generated based on the collective results of the statistical tests, providing a clear, high-level conclusion. The summary output includes the `field_name`, `total_values`, `valid_values`, detailed results from the `chi_square_test`, `ks_test`, and `mean_absolute_deviation`, along with a concluding `summary` string that interprets the combined results.
- **Batch Analysis**: The `batch_analyze` method allows for the efficient analysis of multiple data fields within a single DataFrame, streamlining the process of testing different financial metrics.
- **Visualization**: A `plot_distribution` method is available to generate a side-by-side bar chart comparing the observed first-digit distribution against the theoretical Benford's Law distribution. This offers an intuitive visual representation of the results. The plotting logic is implemented using a `PlotBuilder` class ([`src/utils/plotting.py`](src/utils/plotting.py:7)), which employs an elegant builder pattern. This design allows for a fluent and declarative way to construct complex plots by chaining method calls (e.g., `with_title`, `with_labels`, `add_side_by_side_bars`), making the plotting code more readable and maintainable.


#### Insights

- **Market Capitalization**: Regardless of the `get_market_cap` method used (direct fetching or manual calculation), the market capitalization data for S&P 500 constituents is expected to conform to Benford's Law. This is because the analysis only considers the first digit of the values, which is not significantly affected by minor differences in calculation methods. Both approaches produce large, naturally occurring numbers that span several orders of magnitude, which is the ideal condition for Benford's Law to apply.

- **Payout Ratio**: The `payoutRatio` is a financial metric that does not adhere to Benford's Law. This is because the `payoutRatio` is constrained by clear minimum and maximum boundaries (typically between 0 and 1), which violates the fundamental assumption of Benford's Law that the data must be unbounded and span multiple orders of magnitude.

- **Limitations & Evaluation**:
    - **Data Source Reliability**: The constituent list is scraped from Wikipedia, which is not a stable data source. The list can change at any time, potentially affecting the analysis.
    - **Survivorship Bias**: The analysis is performed on the current list of S&P 500 companies. This introduces survivorship bias, as it excludes companies that have been delisted due to poor performance. A more robust analysis would include historical constituent data.
    - **Static Analysis**: The current analysis is a snapshot at a single point in time. A time-series analysis of market capitalization could reveal interesting trends and shifts in conformity to Benford's Law over time.

- **Analysis Notebook**: The complete analysis can be found in the Jupyter notebook: [`notebook/end_to_end.ipynb`](notebook/end_to_end.ipynb).


---


### Setup Guide

1. Clone the Repository
```bash
git clone https://github.com/whanyu1212/ft5009-assignment1.git
```

2. Install Poetry for dependency management
```bash
curl -sSL https://install.python-poetry.org | python3 -
```
> Note: If the above command does not work (due to updates or whatsoever), please refer to the [official documentation](https://python-poetry.org/docs/#installation) for the most up-to-date installation instructions.

3. Sync dependencies (It also installs the current project in dev mode)
```bash
poetry install
```

4. Activate virtual environment
```bash
poetry shell
```

5. Install jupyter kernel
```bash
# You can change the name and display name according to your preference
python -m ipykernel install --user --name ft5009 --display-name "ft5009"
```

6. Set up environment variables
```bash
# Copy the example environment file
cp .env.example .env

# Open .env file and replace the placeholder values with your actual credentials
# You can use any text editor, here using VS Code
code .env
```

Make sure to replace all placeholder values in the `.env` file with your actual API keys and credentials. Never commit the `.env` file to version control.

Remark: pre-commit hooks are omitted for simplicity since this is just a simple exercise
---

### Usage
To run the analysis, you can either run the main script or use the jupyter notebooks.

1. Run the main script (Work in progress, placeholder for now)
```bash
python main.py
```

2. Use the jupyter notebooks
- `notebook/end_to_end.ipynb`: This notebook contains the full end-to-end analysis.
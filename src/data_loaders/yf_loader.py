import yfinance as yf
import pandas as pd
import time
from typing import List, Union, Optional, Any


class YFinanceLoader:
    def __init__(self, max_retries: int = 3, delay: float = 1.0):
        self.max_retries = max_retries
        self.delay = delay

    def get_stock_info(
        self,
        tickers: Union[List[str], str],
        fields: Union[List[str], None] = None,
        as_dataframe: bool = True,
    ) -> Union[pd.DataFrame, List[dict]]:
        """Fetch stock information from Yahoo Finance.

        Args:
            tickers (Union[List[str], str]): The stock ticker symbols to fetch data for.
            fields (Union[List[str], None], optional): The specific fields to retrieve. Defaults to None.
            as_dataframe (bool, optional): Whether to return the data as a DataFrame. Defaults to True.

        Returns:
            Union[pd.DataFrame, List[dict]]: The stock information, either as a DataFrame or a list of dictionaries.
        """

        if isinstance(tickers, str):
            tickers = [tickers]

        stock_data = []
        for ticker in tickers:
            for attempt in range(self.max_retries):
                try:
                    data = yf.Ticker(ticker).info

                    if fields:
                        filtered_data = {
                            field: data.get(field, None) for field in fields
                        }
                        # keep the symbol so we can group by it later
                        filtered_data["symbol"] = ticker
                        stock_data.append(filtered_data)
                    else:
                        stock_data.append(data)
                    break  # Success, exit retry loop
                except Exception as e:
                    print(
                        f"Error fetching data for {ticker} (attempt {attempt + 1}/{self.max_retries}): {e}"
                    )
                    if attempt < self.max_retries - 1:
                        time.sleep(self.delay)
                    else:
                        print(
                            f"Failed to fetch data for {ticker} after {self.max_retries} attempts."
                        )

        if as_dataframe:
            return pd.DataFrame(stock_data)
        return stock_data

    def get_stock_info_value(
        self,
        stock_info_df: pd.DataFrame,
        field_pattern: str,
        exact_match: bool = True,
    ) -> Optional[Any]:
        """Get a field value from stock info DataFrame by column name pattern.

        Args:
            stock_info_df (pd.DataFrame): The stock info DataFrame
            field_pattern (str): The field name or pattern to search for
            exact_match (bool): If True, match exact column name. If False, match partial pattern

        Returns:
            Optional[Any]: The field value if found, None otherwise
        """
        if exact_match:
            if field_pattern in stock_info_df.columns:
                return stock_info_df[field_pattern]
        else:
            # Find columns that contain the pattern (case-insensitive)
            matching_cols = [
                col
                for col in stock_info_df.columns
                if field_pattern.lower() in col.lower()
            ]
            if matching_cols:
                return stock_info_df[matching_cols[0]]

        return None


# Sample usage
if __name__ == "__main__":
    loader = YFinanceLoader()
    df = loader.get_stock_info("AAPL")
    print(df)

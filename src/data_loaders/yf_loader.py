import yfinance as yf
import pandas as pd
import time
from loguru import logger
from typing import List, Union, Optional, Any
from src.utils.schemas import MarketCapSchema


class YFinanceLoader:
    def __init__(self, max_retries: int = 3, delay: float = 1.0):
        self.max_retries = max_retries
        self.delay = delay

    # * Stock info has 176 columns, probably not worth the effort to define
    # * a schema for data validation
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
                    logger.error(
                        f"Error fetching data for {ticker} (attempt {attempt + 1}/{self.max_retries}): {e}"
                    )
                    if attempt < self.max_retries - 1:
                        time.sleep(self.delay)
                    else:
                        logger.error(
                            f"Failed to fetch data for {ticker} after {self.max_retries} attempts."
                        )

        if as_dataframe:
            return pd.DataFrame(stock_data)
        return stock_data

    # * Not really useful to keep this for a single ticker
    # def get_stock_info_value(
    #     self,
    #     ticker: str,
    #     field: str,
    # ) -> Optional[Any]:
    #     """Get a single field value from stock info.

    #     Args:
    #         ticker (str): The stock ticker symbol.
    #         field (str): The field name to retrieve.

    #     Returns:
    #         Optional[Any]: The field value if found, None otherwise.
    #     """
    #     stock_info = self.get_stock_info(
    #         tickers=ticker, fields=[field], as_dataframe=False
    #     )
    #     if (
    #         stock_info
    #         and isinstance(stock_info, list)
    #         and stock_info[0].get(field) is not None
    #     ):
    #         return stock_info[0][field]
    #     return None

    def get_latest_ohlcv(self, ticker: str) -> Optional[pd.DataFrame]:
        """Get the latest OHLCV (Open, High, Low, Close, Volume) data for a given stock ticker.

        Args:
            ticker (str): The stock ticker symbol.

        Returns:
            Optional[pd.DataFrame]: The latest OHLCV data as a DataFrame if found, None otherwise.
        """
        try:
            ohlcv = yf.download(
                ticker, period="1d", interval="1m", auto_adjust=True, progress=False
            )
            # Fix the multi-level column issue
            ohlcv.columns = [i[0] for i in ohlcv.columns]
            ohlcv.reset_index(inplace=True)
            return ohlcv
        except Exception as e:
            logger.error(f"Error fetching OHLCV data for {ticker}: {e}")
            return None

    # ! Might hit a rate limit if we call this too often
    def get_market_cap(
        self, tickers: Union[List[str], str], prefer_calc: bool = False
    ) -> pd.DataFrame:
        """
        Get the market cap for given stock tickers.

        It can fetch the market cap directly from stock info or calculate it
        from the latest price and shares outstanding.

        Args:
            tickers (Union[List[str], str]): The stock ticker symbols.
            prefer_calc (bool): If True, prioritize calculation over direct fetching.
                                Defaults to False.

        Returns:
            pd.DataFrame: DataFrame with ticker and marketCap.
        """
        if isinstance(tickers, str):
            tickers = [tickers]

        market_caps = []

        # Fetch required data in a more efficient way
        fields_to_fetch = ["marketCap", "sharesOutstanding"]
        stock_info_list = self.get_stock_info(
            tickers=tickers, fields=fields_to_fetch, as_dataframe=False
        )

        stock_info_map = {info["symbol"]: info for info in stock_info_list}

        for ticker in tickers:
            market_cap = None
            info = stock_info_map.get(ticker)

            if not info:
                market_caps.append({"symbol": ticker, "marketCap": None})
                continue

            # Option 1: Use calculated market cap if preferred or direct is unavailable
            # ! More accurate but introduces performance overhead
            if prefer_calc or info.get("marketCap") is None:
                shares = info.get("sharesOutstanding")
                if shares:
                    ohlcv = self.get_latest_ohlcv(ticker)
                    if ohlcv is not None and not ohlcv.empty:
                        latest_price = ohlcv.iloc[-1]["Close"]
                        market_cap = latest_price * shares

            # Option 2: Use market cap from info if not calculated
            # !IMPORTANT: This may not always be accurate or up-to-date
            if market_cap is None:
                market_cap = info.get("marketCap")

            market_caps.append({"symbol": ticker, "marketCap": market_cap})

        df = pd.DataFrame(market_caps).dropna()
        try:
            MarketCapSchema.validate(df)
            logger.info("Market cap data validation successful.")
        except Exception as e:
            logger.warning(f"Market cap data failed validation: {e}")
        return df

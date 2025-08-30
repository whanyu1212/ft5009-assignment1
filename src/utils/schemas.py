import pandas as pd
import pandera as pa
from datetime import datetime

current_year = datetime.now().year


def is_valid_date(date_series):
    """Check if date strings in Series are valid YYYY-MM-DD format or null"""

    def check_single_date(date_str):
        if pd.isna(date_str):
            return True
        try:
            datetime.strptime(str(date_str), "%Y-%m-%d")
            return True
        except (ValueError, TypeError):
            return False

    # Apply the check to each element and return True if all are valid
    return date_series.apply(check_single_date).all()


# Classic pandera schema (works with older versions)
SP500ConstituentSchema = pa.DataFrameSchema(
    {
        "Symbol": pa.Column(
            dtype=str,
            unique=True,
            nullable=False,
            description="The ticker symbol for the security.",
        ),
        "Security": pa.Column(
            dtype=str,
            nullable=False,
            description="The name of the security (the company).",
        ),
        "GICS Sector": pa.Column(
            dtype=str,
            nullable=False,
            description="The GICS Sector the company belongs to.",
        ),
        "GICS Sub-Industry": pa.Column(
            dtype=str,
            nullable=False,
            description="The GICS Sub-Industry the company belongs to.",
        ),
        "Headquarters Location": pa.Column(
            dtype=str,
            nullable=False,
            description="The city and state/country of the company's headquarters.",
        ),
        "Date added": pa.Column(
            dtype=str,
            nullable=True,
            checks=pa.Check(is_valid_date, error="date format is not valid"),
            description="The date the company was added to the S&P 500 index.",
        ),
        "CIK": pa.Column(
            dtype=int,
            nullable=False,
            description="The company's Central Index Key (CIK).",
        ),
        "Founded": pa.Column(
            dtype=object,
            nullable=False,
            description="The year the company was founded.",
        ),
    },
    coerce=True,
    strict=True,
)

MarketCapSchema = pa.DataFrameSchema(
    {
        "symbol": pa.Column(
            dtype=str,
            nullable=False,
            description="The ticker symbol for the security.",
        ),
        "marketCap": pa.Column(
            dtype=float,
            nullable=False,
            checks=[
                pa.Check(
                    lambda s: s >= 0,
                    element_wise=True,
                    error="marketCap cannot be negative",
                )
            ],
            description="The market capitalization of the company.",
        ),
    },
    coerce=True,
    strict=True,
)

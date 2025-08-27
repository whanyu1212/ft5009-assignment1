from pydantic import BaseModel, Field, RootModel
from typing import List


class IndividualStock(BaseModel):
    """
    Represents a single constituent company of the S&P 500 index.
    The field names and descriptions are based on the provided S&P 500 components table.
    """

    symbol: str = Field(..., description="The ticker symbol for the security.")
    security: str = Field(..., description="The name of the security (the company).")
    gics_sector: str = Field(
        ...,
        description="The Global Industry Classification Standard (GICS) Sector the company belongs to.",
    )
    gics_sub_industry: str = Field(
        ...,
        description="The Global Industry Classification Standard (GICS) Sub-Industry the company belongs to.",
    )
    headquarters_location: str = Field(
        ..., description="The city and state/country of the company's headquarters."
    )
    date_added: str = Field(
        ..., description="The date the company was added to the S&P 500 index."
    )
    cik: str = Field(
        ..., description="The company's Central Index Key (CIK) assigned by the SEC."
    )
    founded: str = Field(..., description="The year the company was founded.")


class SP500Constituents(RootModel[List[IndividualStock]]):
    root: List[IndividualStock]

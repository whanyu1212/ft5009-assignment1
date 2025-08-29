import pandas as pd
from loguru import logger
from schemas import SP500ConstituentSchema


def validate_sp500_constituents(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process the S&P 500 constituents DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        pd.DataFrame: The processed DataFrame.
    """
    # Validate the DataFrame against the schema
    validated_df = SP500ConstituentSchema.validate(df)
    logger.info(
        f"Successfully validated DataFrame with {len(validated_df)} rows against SP500ConstituentSchema"
    )

    # Log and drop missing values
    missing_values = validated_df[validated_df.isnull().any(axis=1)]
    if not missing_values.empty:
        logger.info(
            f"Found and dropped {len(missing_values)} rows with missing values."
        )
        logger.info(f"Missing rows:\n{missing_values}")
        validated_df = validated_df.dropna()

    # Log and drop duplicates
    duplicates = validated_df[validated_df.duplicated()]
    if not duplicates.empty:
        logger.info(f"Found and dropped {len(duplicates)} duplicate rows.")
        logger.info(f"Duplicate rows:\n{duplicates}")
        validated_df = validated_df.drop_duplicates()

    return validated_df

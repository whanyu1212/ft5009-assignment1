import logging
import pandas as pd
from .base_processor import BaseProcessor
from .schemas import SP500ConstituentSchema

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class SP500Processor(BaseProcessor):
    """
    A data processor for S&P 500 constituents data.

    This processor validates and cleans the S&P 500 constituents DataFrame
    using the SP500ConstituentSchema.
    """

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process the S&P 500 constituents DataFrame.

        Args:
            df (pd.DataFrame): The input DataFrame.

        Returns:
            pd.DataFrame: The processed DataFrame.
        """
        # Validate the DataFrame against the schema
        validated_df = SP500ConstituentSchema.validate(df)
        logging.info(
            f"Successfully validated DataFrame with {len(validated_df)} rows against SP500ConstituentSchema"
        )

        # Log and drop missing values
        missing_values = validated_df[validated_df.isnull().any(axis=1)]
        if not missing_values.empty:
            logging.info(
                f"Found and dropped {len(missing_values)} rows with missing values."
            )
            logging.info(f"Missing rows:\n{missing_values}")
            validated_df = validated_df.dropna()

        # Log and drop duplicates
        duplicates = validated_df[validated_df.duplicated()]
        if not duplicates.empty:
            logging.info(f"Found and dropped {len(duplicates)} duplicate rows.")
            logging.info(f"Duplicate rows:\n{duplicates}")
            validated_df = validated_df.drop_duplicates()

        return validated_df

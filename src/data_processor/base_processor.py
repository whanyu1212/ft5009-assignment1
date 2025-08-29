from abc import ABC, abstractmethod
from typing import Any, Dict

import pandas as pd


class BaseProcessor(ABC):
    """
    An abstract base class for data processors for different
    dataframes
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initializes the data processor.

        Args:
            config (Dict[str, Any], optional): A dictionary of configuration parameters.
                                              Defaults to None.
        """
        self.config = config or {}

    @abstractmethod
    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process the given DataFrame.

        This method should be implemented by subclasses to perform data
        validation, cleaning, transformation, and other processing steps.

        Args:
            df (pd.DataFrame): The input DataFrame to process.

        Returns:
            pd.DataFrame: The processed DataFrame.
        """
        pass

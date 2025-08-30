import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple, Union
from scipy import stats
from loguru import logger
from src.utils.plotting import PlotBuilder


class BenfordsLawAnalyzer:
    """
    Benford's Law states that in many naturally occurring datasets,
    the probability of the first digit being d is log10(1 + 1/d).
    """

    def __init__(self):
        """Initialize the Benford analyzer with the theoretical distribution."""
        self.theoretical_distribution = self._calculate_theoretical_distribution()
        self.observed_distribution = None
        self.field_name = None  # e.g., marketCap
        self.raw_data = None
        self.valid_data = None

    # === private methods ===

    # A bunch of calculations

    def _calculate_theoretical_distribution(self) -> Dict[int, float]:
        """Calculate the theoretical Benford's Law distribution.

        Returns:
            Dict[int, float]: Dictionary mapping first digits (1-9) to their expected probabilities
        """
        return {digit: np.log10(1 + 1 / digit) for digit in range(1, 10)}

    def _calculate_observed_distribution(
        self, first_digits: pd.Series
    ) -> Dict[int, float]:
        """Calculate the observed distribution of first digits.

        Args:
            first_digits (pd.Series): Series containing the first digits.

        Returns:
            Dict[int, float]: Dictionary mapping observed first digits to their proportions.
        """
        if first_digits.empty:
            return {d: 0.0 for d in range(1, 10)}

        digit_counts = first_digits.value_counts()
        total_count = len(first_digits)

        # Initialize observed distribution with all digits from 1 to 9 having a count of 0
        observed_dist = {d: 0.0 for d in range(1, 10)}

        # Update the distribution with the actual counts
        for digit, count in digit_counts.items():
            if 1 <= digit <= 9:
                observed_dist[digit] = count / total_count

        return observed_dist

    def _extract_first_digits(self, data: pd.Series) -> pd.Series:
        """Extract the first digits from a Series of numerical data.

        Args:
            data (pd.Series): Series containing numerical values

        Returns:
            pd.Series: Series containing first digits (1-9)
        """

        # Convert to column to absolute values and remove zeros/nulls
        # Though the NaN values are removed and its unlikely to have negative values,
        # we take the absolute value for safety

        abs_data = data.abs()
        valid_mask = (abs_data > 0) & (~abs_data.isna())
        valid_data = abs_data[valid_mask]

        if len(valid_data) == 0:
            logger.warning("No valid numerical data found after filtering")
            return pd.Series(dtype=int)

        # Extract first digit by converting to string and taking first character
        first_digits = valid_data.astype(str).str[0].astype(int)

        # Filter to only include digits 1-9 (remove any potential issues)
        first_digits = first_digits[first_digits.between(1, 9)]

        logger.info(
            f"Extracted {len(first_digits)} valid first digits from {len(data)} total values"
        )
        return first_digits

    def _chi_square_test(self, alpha: float = 0.05) -> Dict:
        """Perform Chi-square goodness of fit test.

        The Chi-Square goodness-of-fit test is used to determine if there is a significant difference
        between an observed frequency distribution and a theoretical (expected) frequency distribution

        Args:
            alpha (float, optional): Significance level. Defaults to 0.05.

        Raises:
            ValueError: If the observed distribution is not available for testing

        Returns:
            Dict: Chi-square test results
        """

        if self.observed_distribution is None:
            raise ValueError("Must run analyze() first")

        observed_counts = []
        expected_counts = []

        total_observations = len(self.valid_data)

        for digit in range(1, 10):
            observed_freq = self.observed_distribution.get(digit, 0)
            expected_freq = self.theoretical_distribution[digit]

            observed_counts.append(observed_freq * total_observations)
            expected_counts.append(expected_freq * total_observations)

        chi2_stat, p_value = stats.chisquare(observed_counts, expected_counts)

        return {
            "statistic": chi2_stat,
            "p_value": p_value,
            "degrees_of_freedom": 8,  # 9 digits - 1
            "significant": p_value < alpha,
            "interpretation": (
                f"Significantly different from Benford's Law (p < {alpha})"
                if p_value < alpha
                else f"Not significantly different from Benford's Law (p >= {alpha})"
            ),
        }

    def _kolmogorov_smirnov_test(self, confidence_level: float = 0.95) -> Dict:
        """
        Perform Kolmogorov-Smirnov test.

        It is another method to determine if a sample comes from a specific distribution.
        Unlike the Chi-Square test which looks at frequencies, the KS test looks at the cumulative distributions.

        Args:
            confidence_level (float, optional): Confidence level for the test. Defaults to 0.95.

        Returns:
            Dict: KS test results
        """
        if self.observed_distribution is None:
            raise ValueError("Must run analyze() first")

        # Critical value multipliers for different confidence levels
        critical_values_map = {
            0.90: 1.22,
            0.95: 1.36,
            0.99: 1.63,
        }
        if confidence_level not in critical_values_map:
            raise ValueError(
                f"Invalid confidence level. Choose from {list(critical_values_map.keys())}"
            )

        # Calculate cumulative distributions
        observed_cumulative = []
        theoretical_cumulative = []
        cumulative_obs = 0
        cumulative_theo = 0

        for digit in range(1, 10):
            cumulative_obs += self.observed_distribution.get(digit, 0)
            cumulative_theo += self.theoretical_distribution[digit]
            observed_cumulative.append(cumulative_obs)
            theoretical_cumulative.append(cumulative_theo)

        # Calculate KS statistic (maximum difference)
        ks_statistic = max(
            abs(obs - theo)
            for obs, theo in zip(observed_cumulative, theoretical_cumulative)
        )

        # For large samples, approximate p-value
        n = len(self.valid_data)
        critical_value_multiplier = critical_values_map[confidence_level]
        critical_value = critical_value_multiplier / np.sqrt(n)

        return {
            "statistic": ks_statistic,
            "critical_value": critical_value,
            "confidence_level": confidence_level,
            "significant": ks_statistic > critical_value,
            "interpretation": (
                f"Significantly different from Benford's Law at {confidence_level:.0%} confidence"
                if ks_statistic > critical_value
                else f"Not significantly different from Benford's Law at {confidence_level:.0%} confidence"
            ),
        }

    def _mean_absolute_deviation(self) -> Dict:
        """Calculate Mean Absolute Deviation (MAD) from Benford's distribution.

        It is not a formal hypothesis test like the others,
        but rather a measure of the average error or deviation between your data and the theoretical model.

        Raises:
            ValueError: If analysis has not been run

        Returns:
            Dict: MAD results with interpretation
        """

        if self.observed_distribution is None:
            raise ValueError("Must run analyze() first")

        deviations = []
        for digit in range(1, 10):
            observed = self.observed_distribution.get(digit, 0)
            expected = self.theoretical_distribution[digit]
            deviations.append(abs(observed - expected))

        mad = np.mean(deviations)

        # MAD interpretation thresholds (commonly used in literature)
        if mad < 0.006:
            conformity = "Low Dispersion: Indicates a very close fit to Benford's Law."
        elif mad < 0.012:
            conformity = "Acceptable Dispersion: Indicates a good fit to Benford's Law, typical for clean data."
        elif mad < 0.015:
            conformity = "Marginal Dispersion: Suggests some deviation from Benford's Law, which may be acceptable."
        else:
            conformity = "High Dispersion: Indicates significant deviation from Benford's Law, suggesting potential data anomalies."

        return {
            "mad": mad,
            "conformity_level": conformity,
            "interpretation": f"MAD = {mad:.6f} indicates {conformity.lower()}",
        }

    def _generate_summary(
        self, chi2_result: Dict, ks_result: Dict, mad_result: Dict
    ) -> str:
        """Generate a summary interpretation of all tests.

        Args:
            chi2_result (Dict): Chi-square test results
            ks_result (Dict): KS test results
            mad_result (Dict): MAD test results

        Returns:
            str: Summary interpretation
        """

        tests_agree_conformity = sum(
            [
                not chi2_result["significant"],
                not ks_result["significant"],
                mad_result["mad"] < 0.015,
            ]
        )

        if tests_agree_conformity >= 2:
            return f"The data likely follows Benford's Law. {mad_result['conformity_level']} detected."
        else:
            return "The data likely does not follow Benford's Law. Multiple tests indicate deviation."

    # === Public Methods ===

    def analyze(
        self,
        df: pd.DataFrame,
        field: str,
        alpha: float = 0.05,
        ks_confidence: float = 0.95,
    ) -> Dict:
        """Analyze a specific field in the DataFrame for Benford's Law compliance.

        Args:
            df (pd.DataFrame): Input DataFrame
            field (str): Name of the numerical field to analyze
            alpha (float, optional): Significance level for the Chi-square test. Defaults to 0.05.
            ks_confidence (float, optional): Confidence level for the Kolmogorov-Smirnov test. Defaults to 0.95.

        Raises:
            ValueError: If the specified field is not found in the DataFrame
            ValueError: If no valid data is found for analysis

        Returns:
            Dict: Analysis results including distributions, statistics, and test results
        """
        if field not in df.columns:
            raise ValueError(
                f"Field '{field}' not found in DataFrame columns: {list(df.columns)}"
            )

        self.field_name = field
        self.raw_data = df[field].copy()

        # Extract first digits
        first_digits = self._extract_first_digits(self.raw_data)

        if len(first_digits) == 0:
            raise ValueError(
                f"No valid data found in field '{field}' for Benford's Law analysis"
            )

        self.valid_data = first_digits

        # Calculate observed distribution
        self.observed_distribution = self._calculate_observed_distribution(first_digits)

        # Perform statistical tests
        chi_square_result = self._chi_square_test(alpha=alpha)
        ks_test_result = self._kolmogorov_smirnov_test(confidence_level=ks_confidence)
        mad_result = self._mean_absolute_deviation()

        results = {
            "field_name": field,
            "total_values": len(self.raw_data),
            "valid_values": len(first_digits),
            "theoretical_distribution": self.theoretical_distribution,
            "observed_distribution": self.observed_distribution,
            "chi_square_test": chi_square_result,
            "ks_test": ks_test_result,
            "mean_absolute_deviation": mad_result,
            "summary": self._generate_summary(
                chi_square_result, ks_test_result, mad_result
            ),
        }

        return results

    def batch_analyze(
        self,
        df: pd.DataFrame,
        fields: List[str],
        alpha: float = 0.05,
        ks_confidence: float = 0.95,
    ) -> Dict[str, Dict]:
        """Analyze multiple fields in the DataFrame.

        Args:
            df (pd.DataFrame): Input DataFrame
            fields (List[str]): List of field names to analyze
            alpha (float, optional): Significance level for the Chi-square test. Defaults to 0.05.
            ks_confidence (float, optional): Confidence level for the Kolmogorov-Smirnov test. Defaults to 0.95.

        Returns:
            Dict[str, Dict]: Results for each field
        """
        results = {}

        for field in fields:
            try:
                logger.info(f"Analyzing field: {field}")
                results[field] = self.analyze(
                    df, field, alpha=alpha, ks_confidence=ks_confidence
                )
            except Exception as e:
                logger.error(f"Error analyzing field '{field}': {str(e)}")
                results[field] = {"error": str(e)}

        return results

    def plot_distribution(self, show_plot: bool = True) -> Optional[plt.Figure]:
        """Plot the observed vs. theoretical Benford's Law distribution.

        Args:
            show_plot (bool, optional): Whether to display the plot. Defaults to True.

        Raises:
            ValueError: If the observed distribution is not available.

        Returns:
            Optional[plt.Figure]: The matplotlib figure object if show_plot is False.
        """
        if self.observed_distribution is None:
            raise ValueError("Must run analyze() first to generate distributions.")

        labels = list(self.theoretical_distribution.keys())
        theoretical = list(self.theoretical_distribution.values())
        observed = [self.observed_distribution.get(d, 0) for d in labels]

        # Prepare data for side-by-side bar plot
        data = {
            "Digit": labels * 2,
            "Proportion": observed + theoretical,
            "Type": ["Observed"] * len(labels) + ["Theoretical"] * len(labels),
        }
        plot_df = pd.DataFrame(data)

        plot_builder = PlotBuilder(figsize=(12, 7))
        fig = (
            plot_builder.with_title(f"Benford's Law Distribution for {self.field_name}")
            .with_labels("First Digit", "Proportion")
            .add_side_by_side_bars(data=plot_df, x="Digit", y="Proportion", hue="Type")
            .build()
        )

        if show_plot:
            plt.show()
            return None
        return fig

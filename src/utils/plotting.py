import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Dict, Optional


class PlotBuilder:
    """A builder class for creating plots using matplotlib and seaborn."""

    def __init__(self, figsize: tuple = (10, 6)):
        sns.set_style("whitegrid")
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self._title = ""  # Title of the plot
        self._xlabel = ""  # X-axis label
        self._ylabel = ""  # Y-axis label
        self._legend = False

    def with_title(self, title: str) -> "PlotBuilder":
        """Set the plot title.

        Args:
            title (str): Title of the plot.

        Returns:
            PlotBuilder: The PlotBuilder instance.
        """
        self._title = title
        return self

    def with_labels(self, xlabel: str, ylabel: str) -> "PlotBuilder":
        """Set the x and y axis labels.

        Args:
            xlabel (str): Label for the x-axis.
            ylabel (str): Label for the y-axis.

        Returns:
            PlotBuilder: The PlotBuilder instance.
        """
        self._xlabel = xlabel
        self._ylabel = ylabel
        return self

    def with_legend(self) -> "PlotBuilder":
        """Enable the legend.

        Returns:
            PlotBuilder: The PlotBuilder instance.
        """
        self._legend = True
        return self

    def add_side_by_side_bars(
        self, data: pd.DataFrame, x: str, y: str, hue: str
    ) -> "PlotBuilder":
        """Add a side-by-side bar plot to the axes using seaborn.

        Args:
            data (pd.DataFrame): The data source for the plot.
            x (str): The column name for the x-axis.
            y (str): The column name for the y-axis.
            hue (str): The column name for the hue (grouping) variable.

        Returns:
            PlotBuilder: The PlotBuilder instance.
        """
        sns.barplot(data=data, x=x, y=y, hue=hue, ax=self.ax)
        return self

    def build(self) -> plt.Figure:
        """Build and return the plot figure."""
        self.ax.set_title(self._title)
        self.ax.set_xlabel(self._xlabel)
        self.ax.set_ylabel(self._ylabel)
        if self._legend:
            self.ax.legend()
        return self.fig

    # ! The functions below are deprecated
    # def add_bar(
    #     self,
    #     x: pd.Series,
    #     y: pd.Series,
    #     label: Optional[str] = None,
    #     color: Optional[str] = None,
    #     alpha: float = 1.0,
    # ) -> "PlotBuilder":
    #     """Add a bar plot to the axes.

    #     Args:
    #         x (pd.Series): The data for the x-axis.
    #         y (pd.Series): The data for the y-axis.
    #         label (Optional[str], optional): The label for the bar plot. Defaults to None.
    #         color (Optional[str], optional): The color of the bars. Defaults to None.
    #         alpha (float, optional): The transparency level of the bars. Defaults to 1.0.

    #     Returns:
    #         PlotBuilder: The PlotBuilder instance.
    #     """
    #     self.ax.bar(x, y, label=label, color=color, alpha=alpha)
    #     return self

    # def add_line(
    #     self,
    #     x,
    #     y,
    #     label: Optional[str] = None,
    #     color: Optional[str] = None,
    #     marker: Optional[str] = None,
    # ) -> "PlotBuilder":
    #     """Add a line plot to the axes."""
    #     self.ax.plot(x, y, label=label, color=color, marker=marker)
    #     return self

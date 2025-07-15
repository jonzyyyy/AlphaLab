-----

# AlphaLab: A Quantitative Equity Backtesting & Factor Analytics Platform

This project offers a comprehensive, modular Python workflow for systematic equity strategy research, primarily focusing on the **S\&P 500 universe**. It integrates key components for developing and evaluating investment strategies.

-----

## Overview

AlphaLab provides an end-to-end solution for quantitative researchers, analysts, and developers to rapidly prototype and evaluate systematic investment strategies. It covers:

  * **Factor-based Stock Screening**: Utilizes Value (P/E) and Momentum (6-month return) factors for stock selection.
  * **Automated Portfolio Construction**: Creates equal-weight portfolios with scheduled rebalancing.
  * **Historical Backtesting**: Simulates strategy performance and compares it against the S\&P 500 benchmark.
  * **Performance Analytics & Visualization**: Generates cumulative return plots and calculates crucial risk and return statistics.

-----

## Features

  * **Data Ingestion**: Fetches historical price and fundamental data using `yfinance`.
  * **Train/Test Split**: Prevents look-ahead bias by separating in-sample (training) and out-of-sample (testing) periods.
  * **Factor Computation**: Automatically calculates P/E ratio and momentum scores for S\&P 500 stocks.
  * **Stock Selection**: Performs composite ranking and selects top-N stocks based on combined factor scores.
  * **Portfolio Rebalancing**: Supports quarterly (or user-defined) rebalancing with forward-filled weights.
  * **Benchmark Comparison**: Overlays strategy performance against SPY (or ^GSPC) cumulative returns.
  * **Performance Metrics**: Provides total return, annualized return, volatility, and Sharpe ratio.

-----

## Prerequisites

To run AlphaLab, you'll need:

  * **Python 3.8+**
  * **pip** or **conda** package manager
  * **Internet access** for data download via `yfinance`

-----

## Installation

Follow these steps to set up the project:

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/yourusername/equity-backtest-platform.git
    cd equity-backtest-platform
    ```

2.  **Create a virtual environment (optional but recommended)**:

      * **Linux/Mac**:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
      * **Windows**:
        ```bash
        venv\Scripts\activate
        ```

3.  **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

-----

## Usage

Once installed, you can use the platform via the Jupyter Notebook:

1.  **Open the Jupyter Notebook**:

    ```bash
    jupyter notebook Equity_Backtest_Notebook.ipynb
    ```

2.  **Modify parameters** at the top of the notebook, including:

      * `tickers` slice (e.g., `top 25` for demo or `full S&P 500`).
      * Train/test split ratio.
      * Rebalance frequency (e.g., `freq='QS'`, `MS`).

3.  **Run cells sequentially** to execute the workflow:

      * Setup & library imports
      * Download and preprocess data
      * Compute factors and select stocks
      * Backtest portfolio with rebalancing
      * Compute and plot performance metrics
      * Compare against benchmark

-----

## Project Structure

```
├── README.md
├── requirements.txt       # Python dependencies
├── Equity_Backtest_Notebook.ipynb
├── data/                  # (Optional) cached CSVs or raw data
└── utils/                 # Utility scripts (helper functions)
    ├── data_utils.py
    └── backtest_utils.py
```

-----

## Performance Metrics Explained

  * **Total Return**: Represents the overall growth of $1 invested.
  * **Annualized Return**: The geometric average return per year.
  * **Annualized Volatility**: The standard deviation of daily returns scaled to a yearly basis.
  * **Sharpe Ratio**: A measure of risk-adjusted return, calculated as the annualized return divided by the annualized volatility.

-----

## Acknowledgements

  * Data provided by **yfinance**.
  * Backtesting concepts inspired by open-source libraries such as **vectorbt** and **Backtrader**.

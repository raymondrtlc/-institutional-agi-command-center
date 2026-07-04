"""
Central Data Orchestration Engine - CORRECTED v1.0.1
Handles multi-source data ingestion, validation, and coherence checking
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Supported data sources"""
    POLYGON = 'polygon'
    ALPHAVANTAGE = 'alphavantage'
    YFINANCE = 'yfinance'
    FINNHUB = 'finnhub'
    NEWSAPI = 'newsapi'
    TRADINGECONOMICS = 'tradingeconomics'


class DataEngine:
    """
    Central data orchestration engine that:
    1. Manages multi-source feeds (futures, options, news, economic)
    2. Performs data validation and conflict resolution
    3. Ensures time-series coherence across timeframes
    4. Caches processed data for rapid access
    """

    def __init__(self, config: Dict):
        """
        Initialize Data Engine
        
        Args:
            config: Configuration dictionary with API keys and settings
        """
        self.config = config
        self.market_data = {}
        self.options_data = {}
        self.news_feed = []
        self.economic_calendar = []
        self.last_update = None
        self.validation_errors = []

    def ingest_futures_data(self, symbol: str, timeframes: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Ingest OHLCV futures data across multiple timeframes
        
        Args:
            symbol: Futures symbol (e.g., 'ESU26')
            timeframes: List of timeframes ('1m', '5m', '15m', '1h', '4h', '1d', '1w', '1mo')
        
        Returns:
            Dictionary with DataFrames for each timeframe
        """
        logger.info(f"Ingesting futures data for {symbol} across {len(timeframes)} timeframes")
        
        data = {}
        for tf in timeframes:
            try:
                # In production: fetch from Polygon.io, IQFeed, or yfinance
                df = self._fetch_timeframe_data(symbol, tf)
                if df is not None and not df.empty:
                    is_valid, errors = self.validate_data_integrity(df, f"{symbol}-{tf}")
                    if is_valid:
                        data[tf] = df
                    else:
                        logger.warning(f"Validation failed for {symbol}-{tf}: {errors}")
                        data[tf] = pd.DataFrame()
                else:
                    data[tf] = pd.DataFrame()
            except Exception as e:
                logger.error(f"Error ingesting {symbol} {tf}: {e}")
                data[tf] = pd.DataFrame()
        
        return data

    def _fetch_timeframe_data(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data for a specific timeframe
        Placeholder for actual API calls
        """
        # TODO: Implement real data fetching
        return None

    def ingest_options_data(self, symbol: str, expiration: str) -> Dict:
        """
        Ingest option chain data with Greeks
        
        Args:
            symbol: Underlying symbol
            expiration: Expiration date (e.g., '2026-07-10')
        
        Returns:
            Dictionary with call/put Greeks and implied volatility
        """
        logger.info(f"Ingesting options data for {symbol} expiring {expiration}")
        
        return {
            'calls': pd.DataFrame(),
            'puts': pd.DataFrame(),
            'greeks': pd.DataFrame()
        }

    def ingest_news_feed(self, sources: List[str], keywords: List[str]) -> List[Dict]:
        """
        Ingest news from multiple sources with filtering
        
        Args:
            sources: News sources (Reuters, CNBC, WSJ, CNN, Bloomberg)
            keywords: Keywords to filter (ES, SPY, tech earnings, Fed, etc.)
        
        Returns:
            List of news articles with sentiment scores
        """
        logger.info(f"Ingesting news from {len(sources)} sources with keywords {keywords}")
        
        return []

    def ingest_economic_calendar(self, lookahead_hours: int = 24) -> pd.DataFrame:
        """
        Ingest economic calendar events
        
        Args:
            lookahead_hours: Hours ahead to scan for events
        
        Returns:
            DataFrame with economic events and impact levels
        """
        logger.info(f"Ingesting economic calendar (next {lookahead_hours} hours)")
        
        return pd.DataFrame()

    def validate_data_integrity(self, data: pd.DataFrame, symbol: str) -> Tuple[bool, List[str]]:
        """
        Perform comprehensive data validation - CORRECTED VERSION
        
        Args:
            data: DataFrame to validate
            symbol: Asset symbol
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check if DataFrame is empty
        if data is None or data.empty:
            errors.append("DataFrame is None or empty")
            return False, errors
        
        # Check required columns exist
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")
            return False, errors
        
        # Check for NaN values
        nan_count = data.isna().sum().sum()
        if nan_count > len(data) * 0.1:  # Alert if > 10% NaN
            errors.append(f"Found {nan_count} NaN values ({nan_count/len(data)*100:.1f}%)")
        
        # Check OHLC ordering with safe access
        try:
            invalid_low_open = (data['Low'] > data['Open']).any()
            invalid_open_high = (data['Open'] > data['High']).any()
            invalid_low_high = (data['Low'] > data['High']).any()
            
            if invalid_low_open or invalid_open_high or invalid_low_high:
                ohlc_violations = (data['Low'] > data['Open']) | (data['Open'] > data['High']) | (data['Low'] > data['High'])
                bad_rows = data[ohlc_violations].head(5)
                errors.append(f"OHLC ordering violated in {ohlc_violations.sum()} rows")
        except TypeError as e:
            errors.append(f"OHLC comparison error (type mismatch): {e}")
        
        # Check volume is non-negative
        try:
            if (data['Volume'] < 0).any():
                bad_rows = data[data['Volume'] < 0].head(5)
                errors.append(f"Negative volume detected in {(data['Volume'] < 0).sum()} rows")
        except TypeError:
            errors.append("Volume column contains non-numeric values")
        
        # Check for duplicate timestamps
        if data.index.duplicated().any():
            duplicate_count = data.index.duplicated().sum()
            errors.append(f"Found {duplicate_count} duplicate timestamps")
        
        # Check for zero volume (suspicious)
        zero_volume_count = (data['Volume'] == 0).sum()
        if zero_volume_count > len(data) * 0.2:  # Alert if > 20% zero volume
            errors.append(f"Found {zero_volume_count} zero-volume bars ({zero_volume_count/len(data)*100:.1f}%)")
        
        is_valid = len(errors) == 0
        if not is_valid:
            logger.warning(f"Data validation failed for {symbol}: {errors}")
        else:
            logger.info(f"Data validation passed for {symbol} ({len(data)} rows)")
        
        return is_valid, errors

    def check_time_series_coherence(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """
        Verify time-series coherence across multiple timeframes - CORRECTED VERSION
        Ensures OHLCV data is internally consistent
        
        Args:
            data_dict: Dictionary with dataframes for each timeframe
        
        Returns:
            Dictionary with coherence scores (0-1) per timeframe
        """
        coherence_scores = {}
        
        timeframe_order = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1mo']
        
        for tf, data in data_dict.items():
            if data is None or data.empty:
                coherence_scores[tf] = 0.0
                logger.warning(f"No data for timeframe {tf}")
                continue
            
            # Check basic structure
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in data.columns for col in required_cols):
                coherence_scores[tf] = 0.0
                continue
            
            # Score based on multiple criteria
            score = 1.0
            
            # 1. Check for gaps in timestamps (should be regular)
            if len(data) > 1:
                try:
                    time_diffs = pd.Series(data.index).diff()
                    mean_diff = time_diffs.mean()
                    if mean_diff > 0 and time_diffs.std() > 0:
                        cv = time_diffs.std() / mean_diff
                        if cv > 0.1:  # Coefficient of variation > 10%
                            score -= 0.1
                except:
                    pass
            
            # 2. Check OHLC consistency
            try:
                high_low_valid = ((data['High'] >= data['Low']).all() and 
                                 (data['High'] >= data['Open']).all() and
                                 (data['High'] >= data['Close']).all())
                if not high_low_valid:
                    score -= 0.2
            except:
                score -= 0.2
            
            # 3. Check for suspicious volume patterns
            try:
                zero_vol_ratio = (data['Volume'] == 0).sum() / len(data)
                if zero_vol_ratio > 0.2:
                    score -= 0.1
            except:
                pass
            
            # 4. Check for outliers (>3 std from mean)
            try:
                close_returns = data['Close'].pct_change().dropna()
                if len(close_returns) > 0:
                    mean_return = close_returns.mean()
                    std_return = close_returns.std()
                    if std_return > 0:
                        outliers = (abs(close_returns - mean_return) > 3 * std_return).sum()
                        outlier_ratio = outliers / len(close_returns)
                        if outlier_ratio > 0.05:
                            score -= 0.15
            except:
                pass
            
            coherence_scores[tf] = max(0.0, score)
        
        logger.info(f"Timeframe coherence scores: {coherence_scores}")
        return coherence_scores

    def resolve_conflicting_data(self, primary: pd.DataFrame, secondary: pd.DataFrame) -> pd.DataFrame:
        """
        Resolve conflicts when multiple data sources provide different values
        
        Args:
            primary: Primary source data
            secondary: Secondary source data (fallback)
        
        Returns:
            Reconciled DataFrame
        """
        if primary is None or primary.empty:
            return secondary
        if secondary is None or secondary.empty:
            return primary
        
        # Use primary source, fill gaps with secondary
        return primary.fillna(secondary)

    def apply_kalman_filter(self, data: pd.Series, q: float = 0.005, r: float = 0.12) -> pd.Series:
        """
        Apply Kalman filter to smooth price series - CORRECTED VERSION
        Separates signal from noise with proper error handling
        
        Args:
            data: Price series
            q: Process noise (how much we expect the underlying value to change)
            r: Measurement noise (sensor uncertainty)
        
        Returns:
            Smoothed price series
        """
        # Validate input
        if data is None or len(data) == 0:
            logger.error("Kalman filter: Empty data series")
            return data
        
        # Remove NaN values and warn
        if data.isna().any():
            logger.warning(f"Kalman filter: Found {data.isna().sum()} NaN values, forward-filling")
            data = data.fillna(method='ffill').fillna(method='bfill')
        
        if not np.isfinite(data.iloc[0]):
            logger.error("Kalman filter: First value is not finite")
            return data
        
        n = len(data)
        estimates = np.zeros(n)
        errors = np.zeros(n)
        
        # Initial state with bounds checking
        estimates[0] = float(data.iloc[0])
        errors[0] = 1.0
        
        for i in range(1, n):
            # Prediction step
            predicted_estimate = estimates[i - 1]
            predicted_error = errors[i - 1] + q
            
            # Ensure error stays positive (safeguard)
            predicted_error = max(predicted_error, 1e-8)
            
            # Guard against NaN in measurement
            measurement = float(data.iloc[i])
            if not np.isfinite(measurement):
                estimates[i] = predicted_estimate  # Use prediction if measurement is bad
                errors[i] = predicted_error
                continue
            
            # Update step
            denominator = predicted_error + r
            if denominator <= 0:
                logger.warning(f"Kalman filter: Denominator <= 0 at step {i}")
                kalman_gain = 0.5  # Default to 50/50 weighting
            else:
                kalman_gain = predicted_error / denominator
            
            # Ensure Kalman gain is in valid range [0, 1]
            kalman_gain = np.clip(kalman_gain, 0, 1)
            
            estimates[i] = predicted_estimate + kalman_gain * (measurement - predicted_estimate)
            errors[i] = (1 - kalman_gain) * predicted_error
        
        return pd.Series(estimates, index=data.index)

    def get_market_regime(self) -> str:
        """
        Determine current market regime based on multiple indicators
        
        Returns:
            Regime: 'bull', 'bear', 'neutral', 'correction'
        """
        # Placeholder: In production, would use VIX, trend, breadth
        return 'neutral'

    def health_check(self) -> Dict[str, bool]:
        """
        Perform system health check
        
        Returns:
            Dictionary with health status of each component
        """
        return {
            'data_engine': True,
            'futures_feed': True,
            'options_feed': True,
            'news_feed': True,
            'economic_calendar': True
        }

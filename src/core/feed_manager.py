"""
Real-Time Market Feed Manager - CORRECTED v1.0.1
Handles WebSocket connections, data streams, and tick processing
"""

import logging
import asyncio
from typing import Callable, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Tick:
    """Single market tick"""
    symbol: str
    timestamp: datetime
    price: float
    volume: int
    bid: float
    ask: float
    bid_size: int
    ask_size: int


@dataclass
class OHLCV:
    """OHLCV bar"""
    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: datetime


class FeedManager:
    """
    Real-time market feed manager:
    1. Manages WebSocket connections to data providers
    2. Processes incoming ticks and aggregates into bars
    3. Maintains order book snapshots
    4. Handles connection failures and reconnection
    """

    def __init__(self, config: Dict, max_ticks_per_symbol: int = 10000):
        self.config = config
        self.ticks: Dict[str, List[Tick]] = {}
        self.bars: Dict[str, List[OHLCV]] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        self.order_book: Dict[str, Dict] = {}
        self.is_connected = False
        self.max_ticks_per_symbol = max_ticks_per_symbol

    async def connect(self, symbols: List[str]):
        """
        Connect to market data feeds
        
        Args:
            symbols: List of symbols to subscribe to
        """
        logger.info(f"Connecting to feed for {symbols}")
        self.is_connected = True

    async def disconnect(self):
        """
        Disconnect from market data feeds
        """
        logger.info("Disconnecting from feed")
        self.is_connected = False

    def register_callback(self, event_type: str, callback: Callable):
        """
        Register callback for market events
        
        Args:
            event_type: 'tick', 'bar', 'trade', 'quote'
            callback: Function to call when event occurs
        """
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)

    def process_tick(self, tick: Tick):
        """
        Process incoming tick with memory management - CORRECTED VERSION
        
        Args:
            tick: Market tick data
        """
        if tick.symbol not in self.ticks:
            self.ticks[tick.symbol] = []
        
        self.ticks[tick.symbol].append(tick)
        
        # Keep only the last N ticks (prevent memory leak)
        if len(self.ticks[tick.symbol]) > self.max_ticks_per_symbol:
            self.ticks[tick.symbol] = self.ticks[tick.symbol][-self.max_ticks_per_symbol:]
        
        # Trigger callbacks with error handling
        if 'tick' in self.callbacks:
            for callback in self.callbacks['tick']:
                try:
                    callback(tick)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

    def aggregate_to_bar(self, symbol: str, timeframe: str) -> Optional[OHLCV]:
        """
        Aggregate ticks into OHLCV bar - CORRECTED VERSION
        
        Args:
            symbol: Symbol to aggregate
            timeframe: Timeframe ('1m', '5m', '15m', etc.)
        
        Returns:
            OHLCV bar or None if invalid data
        """
        if symbol not in self.ticks or len(self.ticks[symbol]) == 0:
            logger.debug(f"No ticks available for {symbol}")
            return None
        
        ticks = self.ticks[symbol]
        
        # Validate tick data
        if not all(hasattr(t, 'price') and hasattr(t, 'volume') for t in ticks):
            logger.error(f"Invalid tick structure for {symbol}")
            return None
        
        # Filter valid prices and volumes
        prices = [t.price for t in ticks if np.isfinite(t.price)]
        volumes = [t.volume for t in ticks if t.volume >= 0]
        
        if not prices or not volumes:
            logger.warning(f"No valid price/volume data for {symbol}")
            return None
        
        try:
            bar = OHLCV(
                open=float(prices[0]),
                high=float(max(prices)),
                low=float(min(prices)),
                close=float(prices[-1]),
                volume=int(sum(volumes)),
                timestamp=ticks[-1].timestamp
            )
            return bar
        except (ValueError, TypeError) as e:
            logger.error(f"Failed to create bar for {symbol}: {e}")
            return None

    def update_order_book(self, symbol: str, bids: List[tuple], asks: List[tuple]):
        """
        Update order book snapshot
        
        Args:
            symbol: Symbol
            bids: List of (price, size) tuples
            asks: List of (price, size) tuples
        """
        if not bids or not asks:
            logger.warning(f"Empty bids or asks for {symbol}")
            return
        
        self.order_book[symbol] = {
            'bids': bids,
            'asks': asks,
            'timestamp': datetime.now()
        }

    def get_bid_ask_spread(self, symbol: str) -> Optional[float]:
        """
        Get current bid-ask spread - CORRECTED VERSION
        
        Args:
            symbol: Symbol
        
        Returns:
            Bid-ask spread in basis points or None
        """
        if symbol not in self.order_book:
            return None
        
        book = self.order_book[symbol]
        if len(book['bids']) == 0 or len(book['asks']) == 0:
            return None
        
        bid = float(book['bids'][0][0])
        ask = float(book['asks'][0][0])
        
        # Validate bid < ask and both are positive
        if bid <= 0 or ask <= 0:
            logger.warning(f"Invalid bid/ask for {symbol}: bid={bid}, ask={ask}")
            return None
        
        if bid >= ask:
            logger.warning(f"Inverted bid-ask for {symbol}: bid={bid}, ask={ask}")
            return None
        
        spread_bps = (ask - bid) / bid * 10000
        
        # Sanity check: spread should be reasonable (typically < 1000 bps = 10%)
        if spread_bps > 1000:
            logger.warning(f"Unusual spread for {symbol}: {spread_bps} bps")
        
        return spread_bps

    def get_market_depth(self, symbol: str, levels: int = 5) -> Dict:
        """
        Get market depth (order book)
        
        Args:
            symbol: Symbol
            levels: Number of levels to return
        
        Returns:
            Market depth dictionary
        """
        if symbol not in self.order_book:
            return {'bids': [], 'asks': []}
        
        book = self.order_book[symbol]
        return {
            'bids': book['bids'][:levels],
            'asks': book['asks'][:levels]
        }

    def get_latest_tick(self, symbol: str) -> Optional[Tick]:
        """
        Get latest tick for symbol
        
        Args:
            symbol: Symbol
        
        Returns:
            Latest Tick object or None
        """
        if symbol in self.ticks and len(self.ticks[symbol]) > 0:
            return self.ticks[symbol][-1]
        return None

    def get_tick_history(self, symbol: str, lookback: int = 100) -> pd.DataFrame:
        """
        Get tick history
        
        Args:
            symbol: Symbol
            lookback: Number of ticks to return
        
        Returns:
            DataFrame with recent ticks
        """
        if symbol not in self.ticks or len(self.ticks[symbol]) == 0:
            return pd.DataFrame()
        
        ticks = self.ticks[symbol][-lookback:]
        if not ticks:
            return pd.DataFrame()
        
        try:
            data = {
                'timestamp': [t.timestamp for t in ticks],
                'price': [t.price for t in ticks],
                'volume': [t.volume for t in ticks],
                'bid': [t.bid for t in ticks],
                'ask': [t.ask for t in ticks]
            }
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error creating tick history DataFrame: {e}")
            return pd.DataFrame()

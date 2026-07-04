"""
Real-Time Market Feed Manager
Handles WebSocket connections, data streams, and tick processing
"""

import logging
import asyncio
from typing import Callable, Dict, List
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

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

    def __init__(self, config: Dict):
        self.config = config
        self.ticks: Dict[str, List[Tick]] = {}
        self.bars: Dict[str, List[OHLCV]] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        self.order_book: Dict[str, Dict] = {}
        self.is_connected = False

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
        Process incoming tick
        
        Args:
            tick: Market tick data
        """
        if tick.symbol not in self.ticks:
            self.ticks[tick.symbol] = []
        
        self.ticks[tick.symbol].append(tick)
        
        # Trigger callbacks
        if 'tick' in self.callbacks:
            for callback in self.callbacks['tick']:
                callback(tick)

    def aggregate_to_bar(self, symbol: str, timeframe: str) -> OHLCV:
        """
        Aggregate ticks into OHLCV bar
        
        Args:
            symbol: Symbol to aggregate
            timeframe: Timeframe ('1m', '5m', '15m', etc.)
        
        Returns:
            OHLCV bar
        """
        if symbol not in self.ticks or len(self.ticks[symbol]) == 0:
            return None
        
        ticks = self.ticks[symbol]
        prices = [t.price for t in ticks]
        volumes = [t.volume for t in ticks]
        
        bar = OHLCV(
            open=prices[0],
            high=max(prices),
            low=min(prices),
            close=prices[-1],
            volume=sum(volumes),
            timestamp=ticks[-1].timestamp
        )
        
        return bar

    def update_order_book(self, symbol: str, bids: List[tuple], asks: List[tuple]):
        """
        Update order book snapshot
        
        Args:
            symbol: Symbol
            bids: List of (price, size) tuples
            asks: List of (price, size) tuples
        """
        self.order_book[symbol] = {
            'bids': bids,
            'asks': asks,
            'timestamp': datetime.now()
        }

    def get_bid_ask_spread(self, symbol: str) -> float:
        """
        Get current bid-ask spread
        
        Args:
            symbol: Symbol
        
        Returns:
            Bid-ask spread in basis points
        """
        if symbol not in self.order_book:
            return None
        
        book = self.order_book[symbol]
        if len(book['bids']) > 0 and len(book['asks']) > 0:
            bid = book['bids'][0][0]
            ask = book['asks'][0][0]
            spread_bps = (ask - bid) / bid * 10000
            return spread_bps
        
        return None

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

    def get_latest_tick(self, symbol: str) -> Tick:
        """
        Get latest tick for symbol
        
        Args:
            symbol: Symbol
        
        Returns:
            Latest Tick object
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
        if symbol not in self.ticks:
            return pd.DataFrame()
        
        ticks = self.ticks[symbol][-lookback:]
        data = {
            'timestamp': [t.timestamp for t in ticks],
            'price': [t.price for t in ticks],
            'volume': [t.volume for t in ticks],
            'bid': [t.bid for t in ticks],
            'ask': [t.ask for t in ticks]
        }
        return pd.DataFrame(data)

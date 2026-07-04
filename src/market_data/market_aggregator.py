"""
Real-Time Market Data Aggregator
Fetches ES futures, MAG7, bonds, FX, oil, gold, sector ETFs, IWM, DOW
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yfinance as yf
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class MarketSnapshot:
    """Real-time market snapshot"""
    timestamp: datetime
    es_futures: float
    es_change_pct: float
    mag7_prices: Dict[str, float]  # NVDA, TSLA, AAPL, MSFT, GOOGL, AMZN, META
    mag7_changes: Dict[str, float]
    spy: float
    iwm: float
    dia: float
    qqq: float
    us10y: float
    us2y: float
    usd_jpy: float
    wti_crude: float
    gold: float
    vix: float
    sector_etfs: Dict[str, float]  # XLK, XLV, XLF, XLE, XLI, XLY, XLRE, XLUV


class MarketDataAggregator:
    """
    Aggregates real-time market data from multiple sources
    """
    
    MAG7_SYMBOLS = ['NVDA', 'TSLA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
    SECTOR_ETFS = {'XLK': 'Tech', 'XLV': 'Healthcare', 'XLF': 'Finance', 
                   'XLE': 'Energy', 'XLI': 'Industrial', 'XLY': 'Consumer',
                   'XLRE': 'RealEstate', 'XUUV': 'Utilities'}
    BOND_SYMBOLS = {'^TNX': 'US10Y', '^TYX': 'US30Y', '^FVX': 'US5Y'}
    FX_SYMBOLS = {'USDJPY=X': 'USD_JPY', 'EURUSD=X': 'EUR_USD', 'GBPUSD=X': 'GBP_USD'}
    COMMODITY_SYMBOLS = {'CL=F': 'WTI_Crude', 'GC=F': 'Gold', 'SI=F': 'Silver'}
    INDICES = {'^GSPC': 'SPX', '^IXIC': 'NDX', 'SPY': 'SPY', 'IWM': 'IWM', 'DIA': 'DIA', 'QQQ': 'QQQ'}
    
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.last_snapshot: Optional[MarketSnapshot] = None
        self.data_history: Dict[str, pd.DataFrame] = {}
    
    async def fetch_real_time_snapshot(self) -> MarketSnapshot:
        """
        Fetch comprehensive real-time market snapshot
        """
        try:
            # Fetch all data in parallel
            es_data, mag7_data, bonds, fx, commodities, indices, vix = await asyncio.gather(
                self._fetch_es_futures(),
                self._fetch_mag7(),
                self._fetch_bonds(),
                self._fetch_fx(),
                self._fetch_commodities(),
                self._fetch_indices(),
                self._fetch_vix()
            )
            
            snapshot = MarketSnapshot(
                timestamp=datetime.now(),
                es_futures=es_data['price'],
                es_change_pct=es_data['change_pct'],
                mag7_prices=mag7_data['prices'],
                mag7_changes=mag7_data['changes'],
                spy=indices['SPY'],
                iwm=indices['IWM'],
                dia=indices['DIA'],
                qqq=indices['QQQ'],
                us10y=bonds['US10Y'],
                us2y=bonds['US2Y'],
                usd_jpy=fx['USD_JPY'],
                wti_crude=commodities['WTI_Crude'],
                gold=commodities['Gold'],
                vix=vix
            )
            
            self.last_snapshot = snapshot
            logger.info(f"Market snapshot captured: ES={es_data['price']}, VIX={vix}")
            return snapshot
            
        except Exception as e:
            logger.error(f"Error fetching market snapshot: {e}")
            return None
    
    async def _fetch_es_futures(self) -> Dict:
        """Fetch ES (E-mini S&P 500) futures"""
        try:
            # ESU26 = ES September 2026
            es = yf.Ticker('ES=F')
            data = es.history(period='1d')
            if data.empty:
                return {'price': 0, 'change_pct': 0}
            
            price = data['Close'].iloc[-1]
            prev_price = data['Close'].iloc[0] if len(data) > 1 else price
            change_pct = ((price - prev_price) / prev_price * 100) if prev_price > 0 else 0
            
            return {'price': float(price), 'change_pct': float(change_pct)}
        except Exception as e:
            logger.error(f"Error fetching ES futures: {e}")
            return {'price': 0, 'change_pct': 0}
    
    async def _fetch_mag7(self) -> Dict:
        """Fetch MAG7 stock prices"""
        try:
            prices = {}
            changes = {}
            
            for symbol in self.MAG7_SYMBOLS:
                stock = yf.Ticker(symbol)
                data = stock.history(period='1d')
                if not data.empty:
                    price = data['Close'].iloc[-1]
                    prev_price = data['Close'].iloc[0] if len(data) > 1 else price
                    change_pct = ((price - prev_price) / prev_price * 100) if prev_price > 0 else 0
                    prices[symbol] = float(price)
                    changes[symbol] = float(change_pct)
            
            return {'prices': prices, 'changes': changes}
        except Exception as e:
            logger.error(f"Error fetching MAG7: {e}")
            return {'prices': {}, 'changes': {}}
    
    async def _fetch_bonds(self) -> Dict:
        """Fetch US Treasury yields"""
        try:
            bonds = {}
            for ticker, label in self.BOND_SYMBOLS.items():
                bond = yf.Ticker(ticker)
                data = bond.history(period='1d')
                if not data.empty:
                    bonds[label] = float(data['Close'].iloc[-1])
            return bonds
        except Exception as e:
            logger.error(f"Error fetching bonds: {e}")
            return {'US10Y': 0, 'US2Y': 0, 'US30Y': 0}
    
    async def _fetch_fx(self) -> Dict:
        """Fetch FX rates"""
        try:
            fx_data = {}
            for ticker, label in self.FX_SYMBOLS.items():
                pair = yf.Ticker(ticker)
                data = pair.history(period='1d')
                if not data.empty:
                    fx_data[label] = float(data['Close'].iloc[-1])
            return fx_data
        except Exception as e:
            logger.error(f"Error fetching FX: {e}")
            return {'USD_JPY': 0, 'EUR_USD': 0, 'GBP_USD': 0}
    
    async def _fetch_commodities(self) -> Dict:
        """Fetch commodity prices"""
        try:
            commodities = {}
            for ticker, label in self.COMMODITY_SYMBOLS.items():
                comm = yf.Ticker(ticker)
                data = comm.history(period='1d')
                if not data.empty:
                    commodities[label] = float(data['Close'].iloc[-1])
            return commodities
        except Exception as e:
            logger.error(f"Error fetching commodities: {e}")
            return {'WTI_Crude': 0, 'Gold': 0, 'Silver': 0}
    
    async def _fetch_indices(self) -> Dict:
        """Fetch major indices"""
        try:
            indices = {}
            for ticker, label in self.INDICES.items():
                idx = yf.Ticker(ticker)
                data = idx.history(period='1d')
                if not data.empty:
                    indices[label] = float(data['Close'].iloc[-1])
            return indices
        except Exception as e:
            logger.error(f"Error fetching indices: {e}")
            return {'SPY': 0, 'IWM': 0, 'DIA': 0, 'QQQ': 0, 'SPX': 0, 'NDX': 0}
    
    async def _fetch_vix(self) -> float:
        """Fetch VIX (Volatility Index)"""
        try:
            vix = yf.Ticker('^VIX')
            data = vix.history(period='1d')
            return float(data['Close'].iloc[-1]) if not data.empty else 0
        except Exception as e:
            logger.error(f"Error fetching VIX: {e}")
            return 0
    
    def get_market_correlations(self, lookback_days: int = 60) -> pd.DataFrame:
        """
        Calculate correlations between key assets
        """
        try:
            symbols = ['SPY', 'TLT', 'GLD', 'DXY', 'VIX']
            data = yf.download(symbols, period=f'{lookback_days}d', progress=False)
            
            if data.empty:
                return pd.DataFrame()
            
            # Calculate daily returns
            returns = data['Adj Close'].pct_change().dropna()
            
            # Calculate correlation matrix
            corr_matrix = returns.corr()
            
            logger.info(f"Market correlations calculated for {len(returns)} days")
            return corr_matrix
        except Exception as e:
            logger.error(f"Error calculating correlations: {e}")
            return pd.DataFrame()
    
    def get_sector_rotation(self) -> Dict[str, float]:
        """
        Analyze sector rotation strength
        """
        try:
            sector_strengths = {}
            for etf, sector_name in self.SECTOR_ETFS.items():
                try:
                    stock = yf.Ticker(etf)
                    data = stock.history(period='5d')
                    if len(data) > 1:
                        # Calculate 5-day momentum
                        momentum = (data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0] * 100
                        sector_strengths[sector_name] = momentum
                except:
                    pass
            return sector_strengths
        except Exception as e:
            logger.error(f"Error calculating sector rotation: {e}")
            return {}
    
    def get_market_breadth(self) -> Dict[str, any]:
        """
        Calculate market breadth indicators
        """
        try:
            # Fetch S&P 500 components (simplified)
            # In production, would use actual tick data
            breadth_data = {
                'advance_decline_ratio': 2.1,  # Placeholder
                'new_highs': 847,
                'new_lows': 23,
                'advancing_volume': 68.5,  # % of volume
                'declining_volume': 31.5
            }
            return breadth_data
        except Exception as e:
            logger.error(f"Error calculating breadth: {e}")
            return {}

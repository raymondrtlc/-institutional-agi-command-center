"""
Institutional AGI Command Center
SPY / ES Futures Real-Time Analysis System
"""

__version__ = '1.0.0'
__author__ = 'Institutional Trading Systems'

from src.core import DataEngine, FeedManager, CacheManager
from src.technical_analysis import *
from src.market_intelligence import *
from src.ml_ensemble import EnsembleForecaster
from src.visualization import Dashboard

__all__ = [
    'DataEngine',
    'FeedManager',
    'CacheManager',
    'EnsembleForecaster',
    'Dashboard'
]

"""
Comprehensive Technical Analysis Engine
Multi-timeframe analysis: candlestick patterns, 量价, 缠论, Wyckoff, support/resistance
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CandlePattern(Enum):
    """Candlestick patterns"""
    HAMMER = 'hammer'
    SHOOTING_STAR = 'shooting_star'
    ENGULFING_BULL = 'engulfing_bull'
    ENGULFING_BEAR = 'engulfing_bear'
    MORNING_STAR = 'morning_star'
    EVENING_STAR = 'evening_star'
    DOJI = 'doji'
    SPINNING_TOP = 'spinning_top'
    MARUBOZU = 'marubozu'
    HARAMI = 'harami'


class ChanLunPattern(Enum):
    """缠论 (Chan Theory) patterns"""
    SETUP = 'setup'  # 笔 - stroke
    STRUCTURE = 'structure'  # 段 - segment
    CENTRAL_ATOM = 'central_atom'  # 中枢 - central atom
    BREAKOUT = 'breakout'
    PULLBACK = 'pullback'


class WyckoffPhase(Enum):
    """Wyckoff market phases"""
    ACCUMULATION = 'accumulation'
    MARKUP = 'markup'
    DISTRIBUTION = 'distribution'
    MARKDOWN = 'markdown'


@dataclass
class TechnicalSignal:
    """Technical analysis signal"""
    timestamp: datetime
    timeframe: str
    signal_type: str  # 'buy', 'sell', 'neutral'
    confidence: float  # 0-1
    price_level: float
    stop_loss: float
    take_profit: float
    reasons: List[str]


class TechnicalAnalyzer:
    """
    Comprehensive technical analysis across multiple methodologies
    """
    
    def __init__(self):
        self.signals_history: List[TechnicalSignal] = []
        self.support_resistance_levels: Dict[str, Tuple[float, float]] = {}
    
    # ===== CANDLESTICK PATTERNS =====
    
    def detect_candlestick_patterns(self, data: pd.DataFrame) -> Dict[str, List]:
        """
        Detect candlestick reversal patterns
        """
        patterns = {}
        try:
            if len(data) < 3:
                return patterns
            
            # Get last 3 candles
            o = data['Open'].tail(3).values
            h = data['High'].tail(3).values
            l = data['Low'].tail(3).values
            c = data['Close'].tail(3).values
            
            # Two-candle patterns
            if len(data) >= 2:
                bullish_eng = self._detect_engulfing_bullish(o[-2:], h[-2:], l[-2:], c[-2:])
                bearish_eng = self._detect_engulfing_bearish(o[-2:], h[-2:], l[-2:], c[-2:])
                hammer = self._detect_hammer(o[-1], h[-1], l[-1], c[-1])
                shooting_star = self._detect_shooting_star(o[-1], h[-1], l[-1], c[-1])
                doji = self._detect_doji(o[-1], h[-1], l[-1], c[-1])
                
                if bullish_eng: patterns['engulfing_bullish'] = bullish_eng
                if bearish_eng: patterns['engulfing_bearish'] = bearish_eng
                if hammer: patterns['hammer'] = hammer
                if shooting_star: patterns['shooting_star'] = shooting_star
                if doji: patterns['doji'] = doji
            
            # Three-candle patterns
            if len(data) >= 3:
                morning_star = self._detect_morning_star(o, h, l, c)
                evening_star = self._detect_evening_star(o, h, l, c)
                harami = self._detect_harami(o[-2:], h[-2:], l[-2:], c[-2:])
                
                if morning_star: patterns['morning_star'] = morning_star
                if evening_star: patterns['evening_star'] = evening_star
                if harami: patterns['harami'] = harami
            
            logger.info(f"Detected candlestick patterns: {list(patterns.keys())}")
            return patterns
        
        except Exception as e:
            logger.error(f"Error detecting candlestick patterns: {e}")
            return {}
    
    def _detect_engulfing_bullish(self, o, h, l, c) -> Optional[dict]:
        """Bullish engulfing: small red, large green"""
        if c[0] > o[0] or c[1] < o[1]:  # First must be red, second green
            return None
        if o[1] < l[0] and c[1] > h[0]:  # Second fully engulfs first
            return {'pattern': 'engulfing_bullish', 'strength': 0.8}
        return None
    
    def _detect_engulfing_bearish(self, o, h, l, c) -> Optional[dict]:
        """Bearish engulfing: small green, large red"""
        if c[0] < o[0] or c[1] > o[1]:  # First must be green, second red
            return None
        if o[1] > h[0] and c[1] < l[0]:  # Second fully engulfs first
            return {'pattern': 'engulfing_bearish', 'strength': 0.8}
        return None
    
    def _detect_hammer(self, o, h, l, c) -> Optional[dict]:
        """Hammer: long lower wick, small body at top"""
        body = abs(c - o)
        lower_wick = o - l if c > o else c - l
        upper_wick = h - max(c, o)
        range_size = h - l
        
        if range_size == 0:
            return None
        
        if lower_wick > 2 * body and upper_wick < body * 0.5 and body < range_size * 0.3:
            return {'pattern': 'hammer', 'strength': 0.7}
        return None
    
    def _detect_shooting_star(self, o, h, l, c) -> Optional[dict]:
        """Shooting star: long upper wick, small body at bottom"""
        body = abs(c - o)
        upper_wick = h - max(c, o)
        lower_wick = min(c, o) - l
        range_size = h - l
        
        if range_size == 0:
            return None
        
        if upper_wick > 2 * body and lower_wick < body * 0.5 and body < range_size * 0.3:
            return {'pattern': 'shooting_star', 'strength': 0.7}
        return None
    
    def _detect_doji(self, o, h, l, c) -> Optional[dict]:
        """Doji: open ≈ close with long wicks"""
        body = abs(c - o)
        range_size = h - l
        
        if range_size == 0 or body / range_size > 0.1:
            return None
        
        return {'pattern': 'doji', 'strength': 0.6}
    
    def _detect_morning_star(self, o, h, l, c) -> Optional[dict]:
        """Morning star: red, small, green (reversal)"""
        if not (c[0] < o[0] and c[2] > o[2]):  # Red, then green
            return None
        if abs(c[1] - o[1]) < abs(c[0] - o[0]) * 0.5:  # Middle candle small
            return {'pattern': 'morning_star', 'strength': 0.8}
        return None
    
    def _detect_evening_star(self, o, h, l, c) -> Optional[dict]:
        """Evening star: green, small, red (reversal)"""
        if not (c[0] > o[0] and c[2] < o[2]):  # Green, then red
            return None
        if abs(c[1] - o[1]) < abs(c[0] - o[0]) * 0.5:  # Middle candle small
            return {'pattern': 'evening_star', 'strength': 0.8}
        return None
    
    def _detect_harami(self, o, h, l, c) -> Optional[dict]:
        """Harami: large, then small (inside) candle"""
        range1 = h[0] - l[0]
        range2 = h[1] - l[1]
        
        if range1 == 0:
            return None
        
        if range2 < range1 * 0.5 and l[1] > l[0] and h[1] < h[0]:
            return {'pattern': 'harami', 'strength': 0.65}
        return None
    
    # ===== 量价分析 (Price-Volume Analysis) =====
    
    def analyze_price_volume(self, data: pd.DataFrame) -> Dict:
        """
        Analyze price-volume dynamics (量价)
        """
        try:
            if len(data) < 20:
                return {}
            
            # Calculate average volume
            avg_vol = data['Volume'].tail(20).mean()
            last_vol = data['Volume'].iloc[-1]
            vol_ratio = last_vol / avg_vol if avg_vol > 0 else 1.0
            
            # Price change
            price_change = data['Close'].iloc[-1] - data['Close'].iloc[-2]
            
            signals = {
                'price_up_high_vol': price_change > 0 and vol_ratio > 1.2,  # 放量上涨
                'price_up_low_vol': price_change > 0 and vol_ratio < 0.8,   # 缩量上涨
                'price_down_high_vol': price_change < 0 and vol_ratio > 1.2,  # 放量下跌
                'price_down_low_vol': price_change < 0 and vol_ratio < 0.8,  # 缩量下跌
                'volume_ratio': vol_ratio,
                'price_change': price_change
            }
            
            logger.info(f"Price-volume analysis: {signals}")
            return signals
        
        except Exception as e:
            logger.error(f"Error analyzing price-volume: {e}")
            return {}
    
    # ===== 缠论 (Chan Theory) =====
    
    def detect_chanlun_patterns(self, data: pd.DataFrame) -> Dict:
        """
        Detect 缠论 patterns: setups, structures, central atoms
        """
        try:
            if len(data) < 5:
                return {}
            
            # Find local extremes
            highs = data['High'].values
            lows = data['Low'].values
            closes = data['Close'].values
            
            # Identify 笔 (strokes): alternating highs and lows
            strokes = self._identify_strokes(highs, lows)
            
            # Identify 段 (segments): groups of strokes
            segments = self._identify_segments(strokes)
            
            # Identify 中枢 (central atoms): overlapping segments
            central_atoms = self._identify_central_atoms(segments, closes)
            
            patterns = {
                'strokes': len(strokes),
                'segments': len(segments),
                'central_atoms': len(central_atoms),
                'trend': self._determine_trend(closes)
            }
            
            logger.info(f"Chanlun patterns: {patterns}")
            return patterns
        
        except Exception as e:
            logger.error(f"Error detecting chanlun patterns: {e}")
            return {}
    
    def _identify_strokes(self, highs, lows) -> List[dict]:
        """Identify 笔 (strokes)"""
        strokes = []
        # Find alternating local extremes
        for i in range(2, len(highs) - 1):
            # Check for local high
            if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                strokes.append({'type': 'high', 'value': highs[i], 'index': i})
            # Check for local low
            elif lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                strokes.append({'type': 'low', 'value': lows[i], 'index': i})
        return strokes
    
    def _identify_segments(self, strokes) -> List[dict]:
        """Identify 段 (segments): groups of strokes"""
        segments = []
        for i in range(0, len(strokes) - 2, 2):
            if i + 2 < len(strokes):
                segment = {
                    'high': max(strokes[i]['value'], strokes[i+1]['value']),
                    'low': min(strokes[i]['value'], strokes[i+1]['value']),
                    'start': i,
                    'end': i + 2
                }
                segments.append(segment)
        return segments
    
    def _identify_central_atoms(self, segments, closes) -> List[dict]:
        """Identify 中枢 (central atoms): overlapping segments"""
        central_atoms = []
        for i in range(len(segments) - 1):
            seg1 = segments[i]
            seg2 = segments[i + 1]
            
            # Check for overlap
            overlap_high = min(seg1['high'], seg2['high'])
            overlap_low = max(seg1['low'], seg2['low'])
            
            if overlap_low < overlap_high:
                central_atoms.append({
                    'high': overlap_high,
                    'low': overlap_low,
                    'range': overlap_high - overlap_low
                })
        return central_atoms
    
    def _determine_trend(self, closes) -> str:
        """Determine trend direction"""
        if len(closes) < 2:
            return 'unknown'
        sma_short = closes[-5:].mean() if len(closes) >= 5 else closes[-1]
        sma_long = closes[-20:].mean() if len(closes) >= 20 else closes[-1]
        
        if sma_short > sma_long:
            return 'up'
        elif sma_short < sma_long:
            return 'down'
        else:
            return 'neutral'
    
    # ===== WYCKOFF ANALYSIS =====
    
    def analyze_wyckoff_phase(self, data: pd.DataFrame) -> Dict:
        """
        Identify Wyckoff accumulation/distribution phases
        """
        try:
            if len(data) < 50:
                return {}
            
            closes = data['Close'].values
            volumes = data['Volume'].values
            
            # Calculate price range
            recent_high = closes[-20:].max()
            recent_low = closes[-20:].min()
            recent_range = recent_high - recent_low
            
            # Analyze distribution patterns
            distribution_score = self._calculate_distribution_score(closes, volumes)
            accumulation_score = self._calculate_accumulation_score(closes, volumes)
            
            phase = 'neutral'
            if distribution_score > 0.7:
                phase = 'distribution'
            elif accumulation_score > 0.7:
                phase = 'accumulation'
            elif closes[-1] > closes[-20]:
                phase = 'markup'
            elif closes[-1] < closes[-20]:
                phase = 'markdown'
            
            return {
                'phase': phase,
                'distribution_score': distribution_score,
                'accumulation_score': accumulation_score,
                'recent_range': recent_range
            }
        
        except Exception as e:
            logger.error(f"Error analyzing Wyckoff: {e}")
            return {}
    
    def _calculate_distribution_score(self, closes, volumes) -> float:
        """Score for distribution phase (selling at resistance)"""
        if len(closes) < 10:
            return 0.0
        
        recent = closes[-10:]
        recent_vol = volumes[-10:]
        
        # Higher prices with declining volume = distribution
        price_trend = (recent[-1] - recent[0]) / recent[0] if recent[0] > 0 else 0
        volume_trend = (recent_vol[-1] - recent_vol[0].mean()) / recent_vol[0].mean() if recent_vol[0].mean() > 0 else 0
        
        # Distribution: prices up but volume down
        score = max(0, (price_trend - volume_trend) / 2)
        return min(1.0, score)
    
    def _calculate_accumulation_score(self, closes, volumes) -> float:
        """Score for accumulation phase (buying at support)"""
        if len(closes) < 10:
            return 0.0
        
        recent = closes[-10:]
        recent_vol = volumes[-10:]
        
        # Lower prices with increasing volume = accumulation
        price_trend = (recent[0] - recent[-1]) / recent[0] if recent[0] > 0 else 0
        volume_trend = (recent_vol[-1].mean() - recent_vol[0]) / recent_vol[0] if recent_vol[0] > 0 else 0
        
        # Accumulation: prices down but volume up
        score = max(0, (price_trend + volume_trend) / 2)
        return min(1.0, score)
    
    # ===== SUPPORT & RESISTANCE =====
    
    def find_support_resistance(self, data: pd.DataFrame, lookback: int = 50) -> Tuple[float, float]:
        """
        Find key support and resistance levels
        """
        try:
            if len(data) < lookback:
                return None, None
            
            recent = data.tail(lookback)
            highs = recent['High'].values
            lows = recent['Low'].values
            
            # Find major resistance (recent high with rejection)
            resistance = highs.max()
            
            # Find major support (recent low with bounce)
            support = lows.min()
            
            self.support_resistance_levels[data.index[-1]] = (support, resistance)
            
            logger.info(f"Support: {support:.2f}, Resistance: {resistance:.2f}")
            return support, resistance
        
        except Exception as e:
            logger.error(f"Error finding support/resistance: {e}")
            return None, None
    
    def generate_technical_signal(self, data: pd.DataFrame, 
                                 timeframe: str) -> Optional[TechnicalSignal]:
        """
        Generate comprehensive technical signal combining all analyses
        """
        try:
            if data.empty or len(data) < 5:
                return None
            
            current_price = data['Close'].iloc[-1]
            support, resistance = self.find_support_resistance(data)
            
            # Combine all signals
            reasons = []
            score = 0  # -1 (sell) to +1 (buy)
            
            # Candlestick patterns
            patterns = self.detect_candlestick_patterns(data)
            if 'engulfing_bullish' in patterns or 'morning_star' in patterns:
                score += 0.3
                reasons.append("Bullish candlestick pattern")
            if 'engulfing_bearish' in patterns or 'evening_star' in patterns:
                score -= 0.3
                reasons.append("Bearish candlestick pattern")
            
            # Price-volume
            pv = self.analyze_price_volume(data)
            if pv.get('price_up_high_vol'):
                score += 0.2
                reasons.append("Bullish volume increase")
            if pv.get('price_down_high_vol'):
                score -= 0.2
                reasons.append("Bearish volume increase")
            
            # Determine signal
            if score > 0.4:
                signal_type = 'buy'
                stop_loss = support if support else current_price * 0.98
                take_profit = resistance if resistance else current_price * 1.02
            elif score < -0.4:
                signal_type = 'sell'
                stop_loss = resistance if resistance else current_price * 1.02
                take_profit = support if support else current_price * 0.98
            else:
                signal_type = 'neutral'
                stop_loss = support if support else current_price * 0.97
                take_profit = resistance if resistance else current_price * 1.03
            
            confidence = min(1.0, abs(score))
            
            signal = TechnicalSignal(
                timestamp=datetime.now(),
                timeframe=timeframe,
                signal_type=signal_type,
                confidence=confidence,
                price_level=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reasons=reasons
            )
            
            self.signals_history.append(signal)
            logger.info(f"Technical signal for {timeframe}: {signal_type} (confidence: {confidence:.2f})")
            return signal
        
        except Exception as e:
            logger.error(f"Error generating technical signal: {e}")
            return None

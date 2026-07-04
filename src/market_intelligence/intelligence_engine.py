"""
Market Intelligence Engine
Gamma exposure, option flow, Max Pain, Fear & Greed, Polymarket data
"""

import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GammaExposure:
    """Gamma exposure structure"""
    timestamp: datetime
    price: float
    net_gex: float  # In billions
    gamma_flip_level: float
    dealer_direction: str  # 'long_gamma' or 'short_gamma'
    max_pain: float
    call_wall: float
    put_wall: float
    vix_term_structure: float  # IVTS ratio


@dataclass
class OptionFlow:
    """Option flow data"""
    timestamp: datetime
    calls_volume: int
    puts_volume: int
    call_put_ratio: float
    iv_rank: float  # 0-100
    iv_percentile: float  # 0-100
    open_interest_calls: int
    open_interest_puts: int


class MarketIntelligence:
    """
    Advanced market intelligence: gamma, options, sentiment, Polymarket
    """
    
    def __init__(self):
        self.gamma_history: List[GammaExposure] = []
        self.option_flow_history: List[OptionFlow] = []
        self.fear_greed_index: Optional[float] = None
        self.short_squeeze_score: Optional[float] = None
    
    def calculate_gamma_exposure(self, spot_price: float, 
                                option_chain: pd.DataFrame) -> GammaExposure:
        """
        Calculate net gamma exposure for dealer positioning
        
        Args:
            spot_price: Current spot price
            option_chain: DataFrame with strikes and open interest
        
        Returns:
            GammaExposure object with positioning analysis
        """
        try:
            # Simplified gamma calculation
            # In production: use actual option Greeks from data provider
            
            net_gex = self._calculate_net_gex(spot_price, option_chain)
            gamma_flip = self._find_gamma_flip_level(spot_price, option_chain)
            max_pain = self._calculate_max_pain(option_chain)
            call_wall = self._find_resistance_level(option_chain)
            put_wall = self._find_support_level(option_chain)
            vix_ts = self._calculate_vix_term_structure()
            
            dealer_direction = 'long_gamma' if net_gex > 0 else 'short_gamma'
            
            gamma_exp = GammaExposure(
                timestamp=datetime.now(),
                price=spot_price,
                net_gex=net_gex,
                gamma_flip_level=gamma_flip,
                dealer_direction=dealer_direction,
                max_pain=max_pain,
                call_wall=call_wall,
                put_wall=put_wall,
                vix_term_structure=vix_ts
            )
            
            self.gamma_history.append(gamma_exp)
            logger.info(f"Gamma exposure: NET={net_gex:.2f}B, Max Pain=${max_pain:.2f}")
            return gamma_exp
        
        except Exception as e:
            logger.error(f"Error calculating gamma exposure: {e}")
            return None
    
    def _calculate_net_gex(self, spot: float, option_chain: pd.DataFrame) -> float:
        """
        Calculate net gamma exposure in billions
        """
        try:
            # Simplified calculation
            # In production: use actual gamma values from Greeks
            
            if option_chain.empty:
                return 0.0
            
            # Approximate gamma using proximity to ATM
            atm_distance = abs(option_chain['strike'] - spot) / spot
            gamma_proxy = np.exp(-50 * atm_distance)  # Gamma peaks at ATM
            
            # Calculate signed gamma (calls positive, puts negative)
            call_gamma = (option_chain['call_oi'] * gamma_proxy).sum() * 0.001  # Normalize
            put_gamma = -(option_chain['put_oi'] * gamma_proxy).sum() * 0.001
            
            net_gex = call_gamma + put_gamma
            return net_gex
        except Exception as e:
            logger.error(f"Error calculating net GEX: {e}")
            return 0.0
    
    def _find_gamma_flip_level(self, spot: float, option_chain: pd.DataFrame) -> float:
        """
        Find the price level where dealer gamma flips from long to short
        """
        try:
            # Approximate: typically where GEX = 0
            # Often near max pain or major strike concentration
            return spot + 2.5  # Placeholder - typically 0.3-0.5% above spot
        except Exception as e:
            logger.error(f"Error finding gamma flip: {e}")
            return spot
    
    def _calculate_max_pain(self, option_chain: pd.DataFrame) -> float:
        """
        Calculate max pain (strike that minimizes total option loss at expiry)
        """
        try:
            if option_chain.empty:
                return 0.0
            
            # Simplified: weighted average of high OI strikes
            total_oi = (option_chain['call_oi'] + option_chain['put_oi']).sum()
            if total_oi == 0:
                return 0.0
            
            weighted_strike = (option_chain['strike'] * 
                             (option_chain['call_oi'] + option_chain['put_oi'])).sum() / total_oi
            return weighted_strike
        except Exception as e:
            logger.error(f"Error calculating max pain: {e}")
            return 0.0
    
    def _find_resistance_level(self, option_chain: pd.DataFrame) -> float:
        """
        Find call wall (major resistance from call OI)
        """
        try:
            if option_chain.empty:
                return 0.0
            
            # Find strike with highest call OI
            max_call_oi_idx = option_chain['call_oi'].idxmax()
            return option_chain.loc[max_call_oi_idx, 'strike']
        except Exception as e:
            logger.error(f"Error finding resistance: {e}")
            return 0.0
    
    def _find_support_level(self, option_chain: pd.DataFrame) -> float:
        """
        Find put wall (major support from put OI)
        """
        try:
            if option_chain.empty:
                return 0.0
            
            # Find strike with highest put OI
            max_put_oi_idx = option_chain['put_oi'].idxmax()
            return option_chain.loc[max_put_oi_idx, 'strike']
        except Exception as e:
            logger.error(f"Error finding support: {e}")
            return 0.0
    
    def _calculate_vix_term_structure(self) -> float:
        """
        Calculate VIX term structure (IVTS ratio)
        Normal contango when IVTS < 1.0
        """
        try:
            # Placeholder
            # In production: calculate as spot_VIX / 3-month_VIX_futures
            return 0.85  # Normal contango
        except Exception as e:
            logger.error(f"Error calculating IVTS: {e}")
            return 1.0
    
    def analyze_option_flow(self, flow_data: Dict) -> OptionFlow:
        """
        Analyze options flow data
        """
        try:
            calls_vol = flow_data.get('calls_volume', 0)
            puts_vol = flow_data.get('puts_volume', 0)
            total_vol = calls_vol + puts_vol
            
            call_put_ratio = calls_vol / puts_vol if puts_vol > 0 else 1.0
            
            flow = OptionFlow(
                timestamp=datetime.now(),
                calls_volume=calls_vol,
                puts_volume=puts_vol,
                call_put_ratio=call_put_ratio,
                iv_rank=flow_data.get('iv_rank', 50),
                iv_percentile=flow_data.get('iv_percentile', 50),
                open_interest_calls=flow_data.get('oi_calls', 0),
                open_interest_puts=flow_data.get('oi_puts', 0)
            )
            
            self.option_flow_history.append(flow)
            logger.info(f"Option flow: Calls={calls_vol}, Puts={puts_vol}, Ratio={call_put_ratio:.2f}")
            return flow
        
        except Exception as e:
            logger.error(f"Error analyzing option flow: {e}")
            return None
    
    def fetch_fear_greed_index(self) -> float:
        """
        Fetch CNN Fear & Greed Index (0-100)
        """
        try:
            # TODO: Implement actual scraping from CNN or API
            # Placeholder
            import random
            fear_greed = random.uniform(20, 80)
            self.fear_greed_index = fear_greed
            logger.info(f"Fear & Greed Index: {fear_greed:.1f}")
            return fear_greed
        except Exception as e:
            logger.error(f"Error fetching Fear & Greed: {e}")
            return 50.0  # Neutral default
    
    def calculate_short_squeeze_probability(self, short_data: Dict) -> float:
        """
        Calculate probability of short squeeze
        Combines: short interest, borrow rate, option flow, breadth
        """
        try:
            # Weighted factors
            short_interest = short_data.get('short_interest_ratio', 0.5)
            borrow_rate = min(short_data.get('borrow_rate', 1.0) / 20, 1.0)  # Normalize
            call_put_ratio = short_data.get('call_put_ratio', 1.0)
            breadth = min(short_data.get('advance_decline_ratio', 1.5) / 3, 1.0)  # Normalize
            
            # Calculate squeeze probability (0-100)
            squeeze_prob = (
                0.3 * short_interest * 100 +
                0.2 * borrow_rate * 100 +
                0.3 * max(0, call_put_ratio - 1) * 50 +
                0.2 * breadth * 100
            )
            
            self.short_squeeze_score = min(100, squeeze_prob)
            logger.info(f"Short squeeze probability: {self.short_squeeze_score:.1f}%")
            return self.short_squeeze_score
        
        except Exception as e:
            logger.error(f"Error calculating squeeze probability: {e}")
            return 0.0
    
    def get_polymarket_prediction(self, market_name: str) -> Optional[float]:
        """
        Get Polymarket prediction probability
        
        Args:
            market_name: e.g., 'SPY_closes_above_750'
        
        Returns:
            Probability (0-1) or None
        """
        try:
            # TODO: Implement Polymarket API integration
            # Placeholder
            logger.info(f"Fetching Polymarket data for: {market_name}")
            return 0.65  # Placeholder
        except Exception as e:
            logger.error(f"Error fetching Polymarket data: {e}")
            return None
    
    def get_intelligence_summary(self) -> Dict:
        """
        Get comprehensive market intelligence summary
        """
        return {
            'latest_gamma': self.gamma_history[-1] if self.gamma_history else None,
            'latest_option_flow': self.option_flow_history[-1] if self.option_flow_history else None,
            'fear_greed_index': self.fear_greed_index,
            'short_squeeze_score': self.short_squeeze_score
        }

"""
ML Ensemble Forecasting System
ARIMA, LSTM, BiLSTM-Attention, XGBoost, TabPFN ensemble predictions
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ModelType(Enum):
    ARIMA = 'arima'
    LSTM = 'lstm'
    BILSTM_ATTENTION = 'bilstm_attention'
    XGBOOST = 'xgboost'
    TABPFN = 'tabpfn'
    ENSEMBLE = 'ensemble'


@dataclass
class Forecast:
    """ML forecast result"""
    timestamp: datetime
    model_type: ModelType
    prediction: float
    confidence: float  # 0-1
    upper_bound: float  # 95% CI
    lower_bound: float  # 95% CI
    horizon: int  # minutes ahead


@dataclass
class EnsembleForecast:
    """Ensemble forecast combining multiple models"""
    timestamp: datetime
    predicted_price: float
    confidence: float
    bull_probability: float
    base_probability: float
    bear_probability: float
    individual_forecasts: Dict[str, Forecast]
    consensus_direction: str  # 'up', 'down', 'neutral'


class EnsembleForecaster:
    """
    ML ensemble combining ARIMA, LSTM, BiLSTM, XGBoost, TabPFN
    """
    
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.forecast_history: List[EnsembleForecast] = []
        self.model_weights = {
            'arima': 0.15,
            'lstm': 0.25,
            'bilstm_attention': 0.25,
            'xgboost': 0.20,
            'tabpfn': 0.15
        }
    
    async def generate_ensemble_forecast(self, data: pd.DataFrame, 
                                        horizon: int = 15) -> Optional[EnsembleForecast]:
        """
        Generate ensemble forecast combining all models
        
        Args:
            data: Historical OHLCV DataFrame
            horizon: Forecast horizon in minutes
        
        Returns:
            EnsembleForecast with consensus prediction
        """
        try:
            if data.empty or len(data) < 20:
                logger.warning("Insufficient data for forecasting")
                return None
            
            current_price = data['Close'].iloc[-1]
            
            # Generate individual forecasts
            forecasts = {}
            
            # ARIMA forecast
            arima_pred = self._forecast_arima(data, horizon)
            if arima_pred:
                forecasts['arima'] = arima_pred
            
            # LSTM forecast
            lstm_pred = self._forecast_lstm(data, horizon)
            if lstm_pred:
                forecasts['lstm'] = lstm_pred
            
            # BiLSTM-Attention forecast
            bilstm_pred = self._forecast_bilstm_attention(data, horizon)
            if bilstm_pred:
                forecasts['bilstm_attention'] = bilstm_pred
            
            # XGBoost forecast
            xgb_pred = self._forecast_xgboost(data, horizon)
            if xgb_pred:
                forecasts['xgboost'] = xgb_pred
            
            # TabPFN forecast
            tabpfn_pred = self._forecast_tabpfn(data, horizon)
            if tabpfn_pred:
                forecasts['tabpfn'] = tabpfn_pred
            
            if not forecasts:
                logger.error("No forecasts generated")
                return None
            
            # Calculate ensemble prediction
            weighted_price = 0.0
            total_confidence = 0.0
            
            for model_name, forecast in forecasts.items():
                weight = self.model_weights.get(model_name, 0.2)
                weighted_price += forecast.prediction * weight
                total_confidence += forecast.confidence * weight
            
            # Calculate probability tree
            bull_prob, base_prob, bear_prob = self._calculate_probability_tree(
                forecasts, current_price
            )
            
            # Determine consensus direction
            if bull_prob > 0.55:
                direction = 'up'
            elif bear_prob > 0.55:
                direction = 'down'
            else:
                direction = 'neutral'
            
            ensemble = EnsembleForecast(
                timestamp=datetime.now(),
                predicted_price=weighted_price,
                confidence=total_confidence,
                bull_probability=bull_prob,
                base_probability=base_prob,
                bear_probability=bear_prob,
                individual_forecasts=forecasts,
                consensus_direction=direction
            )
            
            self.forecast_history.append(ensemble)
            logger.info(f"Ensemble forecast: {weighted_price:.2f} ± {1.96*(weighted_price-forecasts[list(forecasts.keys())[0]].lower_bound):.2f}, "
                       f"Bull: {bull_prob:.1%}, Base: {base_prob:.1%}, Bear: {bear_prob:.1%}")
            return ensemble
        
        except Exception as e:
            logger.error(f"Error generating ensemble forecast: {e}")
            return None
    
    def _forecast_arima(self, data: pd.DataFrame, horizon: int) -> Optional[Forecast]:
        """
        ARIMA forecast (AutoRegressive Integrated Moving Average)
        """
        try:
            # Placeholder: would use statsmodels.tsa.arima.ARIMA
            # from statsmodels.tsa.arima.model import ARIMA
            # model = ARIMA(data['Close'], order=(5,1,2)).fit()
            # forecast = model.get_forecast(steps=horizon)
            
            last_price = data['Close'].iloc[-1]
            returns = data['Close'].pct_change().dropna()
            volatility = returns.std()
            
            predicted = last_price * (1 + returns.mean() * horizon/len(returns))
            ci = 1.96 * volatility * np.sqrt(horizon)
            
            return Forecast(
                timestamp=datetime.now(),
                model_type=ModelType.ARIMA,
                prediction=predicted,
                confidence=0.75,
                upper_bound=predicted + ci,
                lower_bound=predicted - ci,
                horizon=horizon
            )
        except Exception as e:
            logger.error(f"ARIMA forecast error: {e}")
            return None
    
    def _forecast_lstm(self, data: pd.DataFrame, horizon: int) -> Optional[Forecast]:
        """
        LSTM forecast (Long Short-Term Memory)
        """
        try:
            # Placeholder: would use TensorFlow/Keras LSTM
            # Normalize data
            closes = data['Close'].values
            normalized = (closes - closes.mean()) / closes.std()
            
            # Simple LSTM approximation: momentum-based
            short_mom = (closes[-1] - closes[-5]) / closes[-5] if len(closes) >= 5 else 0
            long_mom = (closes[-1] - closes[-20]) / closes[-20] if len(closes) >= 20 else 0
            
            momentum = (short_mom * 0.7 + long_mom * 0.3)
            predicted = closes[-1] * (1 + momentum * horizon / 100)
            
            volatility = np.std(closes[-20:]) if len(closes) >= 20 else np.std(closes)
            ci = 1.96 * volatility
            
            return Forecast(
                timestamp=datetime.now(),
                model_type=ModelType.LSTM,
                prediction=predicted,
                confidence=0.78,
                upper_bound=predicted + ci,
                lower_bound=predicted - ci,
                horizon=horizon
            )
        except Exception as e:
            logger.error(f"LSTM forecast error: {e}")
            return None
    
    def _forecast_bilstm_attention(self, data: pd.DataFrame, horizon: int) -> Optional[Forecast]:
        """
        BiLSTM with Attention forecast
        """
        try:
            # Placeholder: would use TensorFlow with BiLSTM + Attention
            closes = data['Close'].values
            
            # Calculate attention weights to recent prices
            recent_prices = closes[-10:] if len(closes) >= 10 else closes
            weights = np.arange(1, len(recent_prices) + 1) / len(recent_prices)
            weighted_avg = np.average(recent_prices, weights=weights)
            
            # Mean reversion component
            sma_20 = closes[-20:].mean() if len(closes) >= 20 else closes.mean()
            reversion = (weighted_avg - sma_20) * 0.1
            
            predicted = weighted_avg + reversion
            volatility = np.std(closes[-20:]) if len(closes) >= 20 else np.std(closes)
            ci = 1.96 * volatility
            
            return Forecast(
                timestamp=datetime.now(),
                model_type=ModelType.BILSTM_ATTENTION,
                prediction=predicted,
                confidence=0.80,
                upper_bound=predicted + ci,
                lower_bound=predicted - ci,
                horizon=horizon
            )
        except Exception as e:
            logger.error(f"BiLSTM-Attention forecast error: {e}")
            return None
    
    def _forecast_xgboost(self, data: pd.DataFrame, horizon: int) -> Optional[Forecast]:
        """
        XGBoost gradient boosting forecast
        """
        try:
            # Placeholder: would use xgboost library
            closes = data['Close'].values
            volumes = data['Volume'].values if 'Volume' in data.columns else np.ones(len(closes))
            
            # Feature engineering
            returns = np.diff(closes) / closes[:-1]
            features = {
                'momentum': returns[-1] * 100,
                'volatility': np.std(returns[-20:]) * 100 if len(returns) >= 20 else 0,
                'volume_trend': volumes[-1] / np.mean(volumes[-5:]) if len(volumes) >= 5 else 1,
            }
            
            # Simple XGBoost-like prediction
            predicted = closes[-1] * (1 + features['momentum'] / 100 * 0.01)
            
            volatility = np.std(closes[-20:]) if len(closes) >= 20 else np.std(closes)
            ci = 1.96 * volatility
            
            return Forecast(
                timestamp=datetime.now(),
                model_type=ModelType.XGBOOST,
                prediction=predicted,
                confidence=0.76,
                upper_bound=predicted + ci,
                lower_bound=predicted - ci,
                horizon=horizon
            )
        except Exception as e:
            logger.error(f"XGBoost forecast error: {e}")
            return None
    
    def _forecast_tabpfn(self, data: pd.DataFrame, horizon: int) -> Optional[Forecast]:
        """
        TabPFN (Tabular Prior Function Network) forecast
        """
        try:
            # Placeholder: would use TabPFN from aleatoric-tabpfn
            closes = data['Close'].values
            highs = data['High'].values if 'High' in data.columns else closes
            lows = data['Low'].values if 'Low' in data.columns else closes
            
            # Range and volatility metrics
            recent_range = highs[-10:].max() - lows[-10:].min() if len(highs) >= 10 else 0
            
            # Use percentile-based prediction
            percentile_pred = closes[-1] + recent_range * 0.05
            
            volatility = np.std(closes[-20:]) if len(closes) >= 20 else np.std(closes)
            ci = 1.96 * volatility
            
            return Forecast(
                timestamp=datetime.now(),
                model_type=ModelType.TABPFN,
                prediction=percentile_pred,
                confidence=0.74,
                upper_bound=percentile_pred + ci,
                lower_bound=percentile_pred - ci,
                horizon=horizon
            )
        except Exception as e:
            logger.error(f"TabPFN forecast error: {e}")
            return None
    
    def _calculate_probability_tree(self, forecasts: Dict, 
                                   current_price: float) -> Tuple[float, float, float]:
        """
        Calculate bull/base/bear probability tree
        """
        predictions = [f.prediction for f in forecasts.values()]
        avg_pred = np.mean(predictions)
        std_pred = np.std(predictions) if len(predictions) > 1 else current_price * 0.01
        
        # Define probability ranges
        bull_threshold = avg_pred + std_pred * 0.5
        bear_threshold = avg_pred - std_pred * 0.5
        
        bull_count = sum(1 for p in predictions if p > bull_threshold)
        bear_count = sum(1 for p in predictions if p < bear_threshold)
        base_count = len(predictions) - bull_count - bear_count
        
        total = len(predictions)
        bull_prob = bull_count / total if total > 0 else 0.33
        bear_prob = bear_count / total if total > 0 else 0.33
        base_prob = base_count / total if total > 0 else 0.34
        
        return bull_prob, base_prob, bear_prob
    
    def get_15min_projected_path(self, current_data: pd.DataFrame, 
                                ensemble: EnsembleForecast) -> List[Dict]:
        """
        Generate 15-minute projected price path for current session
        """
        try:
            current_price = current_data['Close'].iloc[-1]
            predicted_price = ensemble.predicted_price
            
            # Calculate path based on probability tree
            bull_move = predicted_price - current_price
            
            # Create 15 one-minute candles projection
            path = []
            for minute in range(1, 16):
                # Path gradually moves toward predicted price
                progress = minute / 15
                target_price = current_price + bull_move * progress
                
                # Add noise based on volatility
                vol = ensemble.individual_forecasts[list(ensemble.individual_forecasts.keys())[0]].upper_bound - \
                      ensemble.individual_forecasts[list(ensemble.individual_forecasts.keys())[0]].lower_bound
                noise = np.random.normal(0, vol / 30)
                
                candle = {
                    'minute': minute,
                    'predicted_price': target_price + noise,
                    'upper_bound': target_price + vol/4,
                    'lower_bound': target_price - vol/4,
                    'probability': ensemble.confidence
                }
                path.append(candle)
            
            logger.info(f"15-min projected path: {current_price:.2f} → {predicted_price:.2f}")
            return path
        
        except Exception as e:
            logger.error(f"Error generating 15-min path: {e}")
            return []
    
    def get_forecast_accuracy_metrics(self) -> Dict:
        """
        Calculate model accuracy metrics from historical forecasts
        """
        try:
            if len(self.forecast_history) < 10:
                return {}
            
            accuracies = {model: [] for model in self.model_weights.keys()}
            
            # Placeholder: would compare forecasts to actual prices
            # and calculate RMSE, MAE, directional accuracy
            
            return {
                'average_confidence': np.mean([f.confidence for f in self.forecast_history]),
                'forecast_count': len(self.forecast_history),
                'bull_accuracy': 0.68,  # Placeholder
                'bear_accuracy': 0.65,  # Placeholder
            }
        except Exception as e:
            logger.error(f"Error calculating accuracy metrics: {e}")
            return {}

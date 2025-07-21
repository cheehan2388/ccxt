"""
Feature Engineering module for processing raw market data and generating derived features.
This module serves as the central hub for all feature calculations and transformations.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
import logging
from abc import ABC, abstractmethod
from datetime import datetime
logger = logging.getLogger(__name__)

# import talib  # Optional - will use manual calculations if not available
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    logger.warning("TA-Lib not available, using manual technical analysis calculations")

class FeatureEngineer(ABC):
    """Abstract base class for feature engineers"""
    
    @abstractmethod
    def calculate_features(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate features from raw data"""
        pass
    
    @abstractmethod
    def get_feature_names(self) -> List[str]:
        """Get list of feature names this engineer produces"""
        pass

class StatisticalFeatureEngineer(FeatureEngineer):
    """Statistical feature engineer for z-scores, percentiles, etc."""
    
    def __init__(self, window_size: int = 20, min_periods: int = 5):
        self.window_size = window_size
        self.min_periods = min_periods
    
    def get_feature_names(self) -> List[str]:
        return [
            'zscore', 'zscore_mean', 'zscore_std', 'zscore_current_value',
            'percentile_rank', 'rolling_mean', 'rolling_std', 'rolling_min', 'rolling_max'
        ]
    
    def calculate_features(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate statistical features"""
        features = {}
        
        try:
            # Ensure we have a numeric column to work with
            if 'open_interest' in data.columns:
                series = data['open_interest']
            elif 'close' in data.columns:
                series = data['close']
            elif 'value' in data.columns:
                series = data['value']
            else:
                # Use first numeric column
                numeric_cols = data.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    series = data[numeric_cols[0]]
                else:
                    return {'valid': False, 'error': 'No numeric columns found'}
            
            if len(series) < self.min_periods:
                return {'valid': False, 'error': f'Insufficient data: {len(series)} < {self.min_periods}'}
            
            # Rolling statistics
            if len(series) >= self.window_size:
                rolling_mean = series.rolling(window=self.window_size, min_periods=self.min_periods).mean()
                rolling_std = series.rolling(window=self.window_size, min_periods=self.min_periods).std()
                rolling_min = series.rolling(window=self.window_size, min_periods=self.min_periods).min()
                rolling_max = series.rolling(window=self.window_size, min_periods=self.min_periods).max()
                
                current_mean = rolling_mean.iloc[-1]
                current_std = rolling_std.iloc[-1]
                current_min = rolling_min.iloc[-1]
                current_max = rolling_max.iloc[-1]
            else:
                current_mean = series.mean()
                current_std = series.std()
                current_min = series.min()
                current_max = series.max()
            
            current_value = series.iloc[-1]
            
            # Z-score calculation
            if current_std == 0 or np.isnan(current_std):
                zscore = 0.0
            else:
                zscore = (current_value - current_mean) / current_std
            
            # Percentile rank
            percentile_rank = (series <= current_value).mean() * 100
            
            features.update({
                'zscore': float(zscore),
                'zscore_mean': float(current_mean),
                'zscore_std': float(current_std),
                'zscore_current_value': float(current_value),
                'percentile_rank': float(percentile_rank),
                'rolling_mean': float(current_mean),
                'rolling_std': float(current_std),
                'rolling_min': float(current_min),
                'rolling_max': float(current_max),
                'valid': True
            })
            
        except Exception as e:
            logger.error(f"Error in statistical feature calculation: {e}")
            features = {'valid': False, 'error': str(e)}
        
        return features

class TechnicalFeatureEngineer(FeatureEngineer):
    """Technical analysis feature engineer"""
    
    def __init__(self, periods: Dict[str, int] = None):
        self.periods = periods or {
            'sma_fast': 5,
            'sma_slow': 20,
            'ema_fast': 12,
            'ema_slow': 26,
            'rsi': 14,
            'bb': 20
        }
    
    def get_feature_names(self) -> List[str]:
        return [
            'sma_fast', 'sma_slow', 'sma_cross', 'sma_distance',
            'ema_fast', 'ema_slow', 'ema_cross', 'ema_distance',
            'rsi', 'rsi_overbought', 'rsi_oversold',
            'bb_upper', 'bb_middle', 'bb_lower', 'bb_position', 'bb_squeeze',
            'price_change', 'price_change_pct', 'volatility'
        ]
    
    def calculate_features(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical analysis features"""
        features = {}
        
        try:
            # Get price series (prefer close, then open_interest, then first numeric)
            if 'close' in data.columns:
                prices = data['close'].values
                price_series = data['close']
            elif 'open_interest' in data.columns:
                prices = data['open_interest'].values
                price_series = data['open_interest']
            else:
                numeric_cols = data.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    prices = data[numeric_cols[0]].values
                    price_series = data[numeric_cols[0]]
                else:
                    return {'valid': False, 'error': 'No price data found'}
            
            if len(prices) < max(self.periods.values()):
                return {'valid': False, 'error': f'Insufficient data for technical analysis'}
            
            if TALIB_AVAILABLE:
                # Use TA-Lib if available
                sma_fast = talib.SMA(prices, timeperiod=self.periods['sma_fast'])
                sma_slow = talib.SMA(prices, timeperiod=self.periods['sma_slow'])
                ema_fast = talib.EMA(prices, timeperiod=self.periods['ema_fast'])
                ema_slow = talib.EMA(prices, timeperiod=self.periods['ema_slow'])
                rsi = talib.RSI(prices, timeperiod=self.periods['rsi'])
                bb_upper, bb_middle, bb_lower = talib.BBANDS(prices, timeperiod=self.periods['bb'])
            else:
                # Manual calculations
                sma_fast = price_series.rolling(window=self.periods['sma_fast']).mean().values
                sma_slow = price_series.rolling(window=self.periods['sma_slow']).mean().values
                
                # Simple EMA calculation
                alpha_fast = 2 / (self.periods['ema_fast'] + 1)
                alpha_slow = 2 / (self.periods['ema_slow'] + 1)
                ema_fast = price_series.ewm(alpha=alpha_fast).mean().values
                ema_slow = price_series.ewm(alpha=alpha_slow).mean().values
                
                # Simple RSI calculation
                rsi = self._calculate_rsi(price_series, self.periods['rsi']).values
                
                # Simple Bollinger Bands
                bb_middle = price_series.rolling(window=self.periods['bb']).mean().values
                bb_std = price_series.rolling(window=self.periods['bb']).std().values
                bb_upper = bb_middle + (bb_std * 2)
                bb_lower = bb_middle - (bb_std * 2)
            
            # Current values
            current_price = prices[-1]
            current_sma_fast = sma_fast[-1] if not np.isnan(sma_fast[-1]) else 0
            current_sma_slow = sma_slow[-1] if not np.isnan(sma_slow[-1]) else 0
            current_ema_fast = ema_fast[-1] if not np.isnan(ema_fast[-1]) else 0
            current_ema_slow = ema_slow[-1] if not np.isnan(ema_slow[-1]) else 0
            current_rsi = rsi[-1] if not np.isnan(rsi[-1]) else 50
            current_bb_upper = bb_upper[-1] if not np.isnan(bb_upper[-1]) else current_price
            current_bb_middle = bb_middle[-1] if not np.isnan(bb_middle[-1]) else current_price
            current_bb_lower = bb_lower[-1] if not np.isnan(bb_lower[-1]) else current_price
            
            # Derived features
            sma_cross = 1 if current_sma_fast > current_sma_slow else -1 if current_sma_fast < current_sma_slow else 0
            ema_cross = 1 if current_ema_fast > current_ema_slow else -1 if current_ema_fast < current_ema_slow else 0
            
            sma_distance = (current_sma_fast - current_sma_slow) / current_sma_slow if current_sma_slow != 0 else 0
            ema_distance = (current_ema_fast - current_ema_slow) / current_ema_slow if current_ema_slow != 0 else 0
            
            bb_width = current_bb_upper - current_bb_lower
            bb_position = (current_price - current_bb_lower) / bb_width if bb_width != 0 else 0.5
            bb_squeeze = 1 if bb_width < np.std(prices[-20:]) * 0.1 else 0
            
            # Price changes
            if len(prices) > 1:
                price_change = current_price - prices[-2]
                price_change_pct = price_change / prices[-2] if prices[-2] != 0 else 0
            else:
                price_change = 0
                price_change_pct = 0
            
            volatility = np.std(prices[-min(20, len(prices)):]) if len(prices) > 1 else 0
            
            features.update({
                'sma_fast': float(current_sma_fast),
                'sma_slow': float(current_sma_slow),
                'sma_cross': int(sma_cross),
                'sma_distance': float(sma_distance),
                'ema_fast': float(current_ema_fast),
                'ema_slow': float(current_ema_slow),
                'ema_cross': int(ema_cross),
                'ema_distance': float(ema_distance),
                'rsi': float(current_rsi),
                'rsi_overbought': int(current_rsi > 70),
                'rsi_oversold': int(current_rsi < 30),
                'bb_upper': float(current_bb_upper),
                'bb_middle': float(current_bb_middle),
                'bb_lower': float(current_bb_lower),
                'bb_position': float(bb_position),
                'bb_squeeze': int(bb_squeeze),
                'price_change': float(price_change),
                'price_change_pct': float(price_change_pct),
                'volatility': float(volatility),
                'current_price': float(current_price),
                'valid': True
            })
            
        except Exception as e:
            logger.error(f"Error in technical feature calculation: {e}")
            features = {'valid': False, 'error': str(e)}
        
        return features
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI manually"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

class VolumeFeatureEngineer(FeatureEngineer):
    """Volume-based feature engineer"""
    
    def __init__(self, window_size: int = 20):
        self.window_size = window_size
    
    def get_feature_names(self) -> List[str]:
        return [
            'volume_mean', 'volume_std', 'volume_ratio', 'volume_spike',
            'vwap', 'volume_trend', 'volume_momentum'
        ]
    
    def calculate_features(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate volume-based features"""
        features = {}
        
        try:
            if 'volume' not in data.columns:
                return {'valid': False, 'error': 'No volume data available'}
            
            volume = data['volume']
            if len(volume) < 2:
                return {'valid': False, 'error': 'Insufficient volume data'}
            
            # Basic volume statistics
            volume_mean = volume.rolling(window=min(self.window_size, len(volume))).mean().iloc[-1]
            volume_std = volume.rolling(window=min(self.window_size, len(volume))).std().iloc[-1]
            current_volume = volume.iloc[-1]
            
            volume_ratio = current_volume / volume_mean if volume_mean != 0 else 1
            volume_spike = 1 if volume_ratio > 2.0 else 0
            
            # VWAP (Volume Weighted Average Price)
            if 'close' in data.columns:
                price = data['close']
                vwap = (price * volume).sum() / volume.sum() if volume.sum() != 0 else price.iloc[-1]
            else:
                vwap = 0
            
            # Volume trend and momentum
            if len(volume) >= 5:
                recent_volume = volume.iloc[-5:].mean()
                older_volume = volume.iloc[-10:-5].mean() if len(volume) >= 10 else volume.iloc[:-5].mean()
                volume_trend = 1 if recent_volume > older_volume else -1 if recent_volume < older_volume else 0
                volume_momentum = (recent_volume - older_volume) / older_volume if older_volume != 0 else 0
            else:
                volume_trend = 0
                volume_momentum = 0
            
            features.update({
                'volume_mean': float(volume_mean),
                'volume_std': float(volume_std),
                'volume_ratio': float(volume_ratio),
                'volume_spike': int(volume_spike),
                'vwap': float(vwap),
                'volume_trend': int(volume_trend),
                'volume_momentum': float(volume_momentum),
                'current_volume': float(current_volume),
                'valid': True
            })
            
        except Exception as e:
            logger.error(f"Error in volume feature calculation: {e}")
            features = {'valid': False, 'error': str(e)}
        
        return features

class FeatureEngineeringManager:
    """Central manager for all feature engineering operations"""
    
    def __init__(self):
        self.engineers: Dict[str, FeatureEngineer] = {}
        self.feature_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        self.cache_ttl = 60  # Cache time-to-live in seconds
    
    def add_engineer(self, name: str, engineer: FeatureEngineer):
        """Add a feature engineer"""
        self.engineers[name] = engineer
        logger.info(f"Added feature engineer: {name}")
    
    def remove_engineer(self, name: str):
        """Remove a feature engineer"""
        if name in self.engineers:
            del self.engineers[name]
            logger.info(f"Removed feature engineer: {name}")
    
    def get_available_features(self) -> Dict[str, List[str]]:
        """Get all available features by engineer"""
        return {name: engineer.get_feature_names() for name, engineer in self.engineers.items()}
    
    def calculate_all_features(self, data: pd.DataFrame, use_cache: bool = True) -> Dict[str, Any]:
        """Calculate features from all registered engineers"""
        cache_key = f"features_{len(data)}_{data.iloc[-1].sum() if len(data) > 0 else 0}"
        
        # Check cache
        if use_cache and cache_key in self.feature_cache:
            cache_time = self.cache_timestamps.get(cache_key, datetime.min)
            if (datetime.now() - cache_time).total_seconds() < self.cache_ttl:
                logger.debug("Using cached features")
                return self.feature_cache[cache_key]
        
        all_features = {
            'timestamp': datetime.now().isoformat(),
            'data_points': len(data),
            'engineers_used': list(self.engineers.keys())
        }
        
        for name, engineer in self.engineers.items():
            try:
                features = engineer.calculate_features(data)
                all_features[name] = features
                logger.debug(f"Calculated features for {name}: {len(features)} features")
            except Exception as e:
                logger.error(f"Error calculating features for {name}: {e}")
                all_features[name] = {'valid': False, 'error': str(e)}
        
        # Cache results
        if use_cache:
            self.feature_cache[cache_key] = all_features
            self.cache_timestamps[cache_key] = datetime.now()
            
            # Clean old cache entries
            self._clean_cache()
        
        return all_features
    
    def calculate_specific_features(self, data: pd.DataFrame, engineer_names: List[str]) -> Dict[str, Any]:
        """Calculate features from specific engineers only"""
        features = {
            'timestamp': datetime.now().isoformat(),
            'data_points': len(data),
            'engineers_used': engineer_names
        }
        
        for name in engineer_names:
            if name in self.engineers:
                try:
                    features[name] = self.engineers[name].calculate_features(data)
                except Exception as e:
                    logger.error(f"Error calculating features for {name}: {e}")
                    features[name] = {'valid': False, 'error': str(e)}
            else:
                logger.warning(f"Engineer {name} not found")
                features[name] = {'valid': False, 'error': f'Engineer {name} not found'}
        
        return features
    
    def get_unified_dataframe(self, data: pd.DataFrame) -> pd.DataFrame:
        """Get a unified DataFrame with all features as columns"""
        features = self.calculate_all_features(data)
        
        # Create a unified feature dictionary
        unified_features = {}
        
        for engineer_name, engineer_features in features.items():
            if engineer_name in ['timestamp', 'data_points', 'engineers_used']:
                continue
                
            if isinstance(engineer_features, dict) and engineer_features.get('valid', False):
                for feature_name, feature_value in engineer_features.items():
                    if feature_name not in ['valid', 'error']:
                        # Prefix with engineer name to avoid conflicts
                        unified_key = f"{engineer_name}_{feature_name}"
                        unified_features[unified_key] = feature_value
        
        # Create DataFrame with features
        feature_df = pd.DataFrame([unified_features])
        
        # Add metadata
        feature_df['timestamp'] = features.get('timestamp')
        feature_df['data_points'] = features.get('data_points')
        
        return feature_df
    
    def _clean_cache(self):
        """Clean expired cache entries"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, timestamp in self.cache_timestamps.items():
            if (current_time - timestamp).total_seconds() > self.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.feature_cache[key]
            del self.cache_timestamps[key]
    
    def clear_cache(self):
        """Clear all cached features"""
        self.feature_cache.clear()
        self.cache_timestamps.clear()
        logger.info("Feature cache cleared")

# Convenience function to create a default feature engineering setup
def create_default_feature_engineering_manager() -> FeatureEngineeringManager:
    """Create a feature engineering manager with default engineers"""
    manager = FeatureEngineeringManager()
    
    # Add default engineers
    manager.add_engineer("statistical", StatisticalFeatureEngineer(window_size=20))
    manager.add_engineer("technical", TechnicalFeatureEngineer())
    manager.add_engineer("volume", VolumeFeatureEngineer())
    
    return manager
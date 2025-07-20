"""
Trading strategy module for making trading decisions based on processed data.
Supports multiple strategies and flexible signal generation.
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
import logging
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

class SignalType(Enum):
    """Trading signal types"""
    LONG = "LONG"
    SHORT = "SHORT"
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"
    HOLD = "HOLD"
    NO_SIGNAL = "NO_SIGNAL"

class TradingSignal:
    """Represents a trading signal"""
    
    def __init__(self, signal_type: SignalType, strength: float = 1.0, 
                 reason: str = "", metadata: Dict = None):
        self.signal_type = signal_type
        self.strength = strength  # Signal strength from 0.0 to 1.0
        self.reason = reason
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
    
    def __str__(self):
        return f"{self.signal_type.value} (strength: {self.strength:.2f}) - {self.reason}"

class Strategy(ABC):
    """Abstract base class for trading strategies"""
    
    @abstractmethod
    def generate_signal(self, processed_data: Dict[str, Any], 
                       current_position: Dict[str, Any] = None) -> TradingSignal:
        """Generate a trading signal based on processed data"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the name of the strategy"""
        pass

class ZScoreStrategy(Strategy):
    """Z-score based trading strategy"""
    
    def __init__(self, long_threshold: float = 1.3, short_threshold: float = -1.3,
                 close_threshold: float = 0.1, min_signal_strength: float = 0.5):
        self.long_threshold = long_threshold
        self.short_threshold = short_threshold
        self.close_threshold = close_threshold
        self.min_signal_strength = min_signal_strength
        
    def get_name(self) -> str:
        return "ZScore"
    
    def generate_signal(self, processed_data: Dict[str, Any], 
                       current_position: Dict[str, Any] = None) -> TradingSignal:
        """
        Generate trading signal based on z-score
        
        Logic:
        - If z-score > long_threshold: LONG signal
        - If z-score < short_threshold: SHORT signal
        - If position exists and z-score approaches 0: CLOSE signal
        - Otherwise: HOLD or NO_SIGNAL
        """
        
        # Extract z-score from processed data
        zscore_data = processed_data.get('zscore', {})
        if not zscore_data.get('valid', False):
            return TradingSignal(SignalType.NO_SIGNAL, 0.0, "Invalid z-score data")
        
        zscore = zscore_data.get('zscore', 0.0)
        current_value = zscore_data.get('value', 0.0)
        
        # Get current position info
        current_side = None
        if current_position:
            current_side = current_position.get('side', None)
            position_size = current_position.get('size', 0.0)
        else:
            position_size = 0.0
        
        # Check for close signals first
        if current_side and abs(zscore) <= self.close_threshold:
            if current_side == 'long':
                strength = min(1.0, (self.long_threshold - zscore) / self.long_threshold)
                return TradingSignal(
                    SignalType.CLOSE_LONG, 
                    strength,
                    f"Z-score returned to neutral: {zscore:.3f}",
                    {'zscore': zscore, 'threshold': self.close_threshold}
                )
            elif current_side == 'short':
                strength = min(1.0, (zscore - self.short_threshold) / abs(self.short_threshold))
                return TradingSignal(
                    SignalType.CLOSE_SHORT, 
                    strength,
                    f"Z-score returned to neutral: {zscore:.3f}",
                    {'zscore': zscore, 'threshold': self.close_threshold}
                )
        
        # Check for new position signals
        if zscore >= self.long_threshold:
            # Calculate signal strength based on how far above threshold
            strength = min(1.0, (zscore - self.long_threshold) / self.long_threshold + 0.5)
            
            if current_side == 'short':
                # Close short and go long
                return TradingSignal(
                    SignalType.CLOSE_SHORT,
                    strength,
                    f"Z-score reversal signal: {zscore:.3f} >= {self.long_threshold}",
                    {'zscore': zscore, 'threshold': self.long_threshold, 'reversal': True}
                )
            elif current_side != 'long' and strength >= self.min_signal_strength:
                return TradingSignal(
                    SignalType.LONG, 
                    strength,
                    f"Z-score long signal: {zscore:.3f} >= {self.long_threshold}",
                    {'zscore': zscore, 'threshold': self.long_threshold}
                )
                
        elif zscore <= self.short_threshold:
            # Calculate signal strength based on how far below threshold
            strength = min(1.0, (abs(zscore) - abs(self.short_threshold)) / abs(self.short_threshold) + 0.5)
            
            if current_side == 'long':
                # Close long and go short
                return TradingSignal(
                    SignalType.CLOSE_LONG,
                    strength,
                    f"Z-score reversal signal: {zscore:.3f} <= {self.short_threshold}",
                    {'zscore': zscore, 'threshold': self.short_threshold, 'reversal': True}
                )
            elif current_side != 'short' and strength >= self.min_signal_strength:
                return TradingSignal(
                    SignalType.SHORT, 
                    strength,
                    f"Z-score short signal: {zscore:.3f} <= {self.short_threshold}",
                    {'zscore': zscore, 'threshold': self.short_threshold}
                )
        
        # No strong signal, hold current position
        if current_side:
            return TradingSignal(
                SignalType.HOLD, 
                0.3,
                f"Holding position, z-score: {zscore:.3f}",
                {'zscore': zscore}
            )
        else:
            return TradingSignal(
                SignalType.NO_SIGNAL, 
                0.0,
                f"No signal, z-score: {zscore:.3f}",
                {'zscore': zscore}
            )

class MeanReversionStrategy(Strategy):
    """Mean reversion strategy using multiple indicators"""
    
    def __init__(self, zscore_threshold: float = 1.5, percentile_threshold: float = 80,
                 ma_deviation_threshold: float = 0.05):
        self.zscore_threshold = zscore_threshold
        self.percentile_threshold = percentile_threshold
        self.ma_deviation_threshold = ma_deviation_threshold
        
    def get_name(self) -> str:
        return "MeanReversion"
    
    def generate_signal(self, processed_data: Dict[str, Any], 
                       current_position: Dict[str, Any] = None) -> TradingSignal:
        """Generate signal based on multiple mean reversion indicators"""
        
        signals = []
        total_strength = 0.0
        reasons = []
        
        # Z-score component
        zscore_data = processed_data.get('zscore', {})
        if zscore_data.get('valid', False):
            zscore = zscore_data.get('zscore', 0.0)
            if abs(zscore) >= self.zscore_threshold:
                signal_type = SignalType.SHORT if zscore > 0 else SignalType.LONG
                strength = min(1.0, abs(zscore) / self.zscore_threshold)
                signals.append((signal_type, strength))
                reasons.append(f"Z-score: {zscore:.3f}")
                total_strength += strength
        
        # Percentile component
        percentile_data = processed_data.get('percentile', {})
        if percentile_data.get('valid', False):
            percentile_rank = percentile_data.get('percentile_rank', 50)
            if percentile_rank >= self.percentile_threshold:
                signals.append((SignalType.SHORT, (percentile_rank - 50) / 50))
                reasons.append(f"Percentile: {percentile_rank:.1f}%")
                total_strength += (percentile_rank - 50) / 50
            elif percentile_rank <= (100 - self.percentile_threshold):
                signals.append((SignalType.LONG, (50 - percentile_rank) / 50))
                reasons.append(f"Percentile: {percentile_rank:.1f}%")
                total_strength += (50 - percentile_rank) / 50
        
        # Moving average deviation component
        ma_data = processed_data.get('ma', {})
        if ma_data.get('valid', False):
            for key, deviation in ma_data.items():
                if key.endswith('_deviation') and abs(deviation) >= self.ma_deviation_threshold:
                    signal_type = SignalType.SHORT if deviation > 0 else SignalType.LONG
                    strength = min(1.0, abs(deviation) / self.ma_deviation_threshold)
                    signals.append((signal_type, strength))
                    reasons.append(f"MA deviation: {deviation:.3f}")
                    total_strength += strength
        
        if not signals:
            return TradingSignal(SignalType.NO_SIGNAL, 0.0, "No mean reversion signals")
        
        # Aggregate signals
        long_strength = sum(s[1] for s in signals if s[0] == SignalType.LONG)
        short_strength = sum(s[1] for s in signals if s[0] == SignalType.SHORT)
        
        if long_strength > short_strength and long_strength > 0.5:
            return TradingSignal(
                SignalType.LONG,
                min(1.0, long_strength / len(signals)),
                f"Mean reversion LONG: {', '.join(reasons)}",
                {'component_signals': signals}
            )
        elif short_strength > long_strength and short_strength > 0.5:
            return TradingSignal(
                SignalType.SHORT,
                min(1.0, short_strength / len(signals)),
                f"Mean reversion SHORT: {', '.join(reasons)}",
                {'component_signals': signals}
            )
        else:
            return TradingSignal(
                SignalType.NO_SIGNAL,
                0.0,
                f"Conflicting signals: {', '.join(reasons)}",
                {'component_signals': signals}
            )

class TrendFollowingStrategy(Strategy):
    """Trend following strategy"""
    
    def __init__(self, ma_period: int = 20, trend_strength_threshold: float = 0.02):
        self.ma_period = ma_period
        self.trend_strength_threshold = trend_strength_threshold
        
    def get_name(self) -> str:
        return "TrendFollowing"
    
    def generate_signal(self, processed_data: Dict[str, Any], 
                       current_position: Dict[str, Any] = None) -> TradingSignal:
        """Generate signal based on trend following logic"""
        
        ma_data = processed_data.get('ma', {})
        if not ma_data.get('valid', False):
            return TradingSignal(SignalType.NO_SIGNAL, 0.0, "No moving average data")
        
        # Look for trend in moving average deviation
        ma_key = f'ma_{self.ma_period}_deviation'
        if ma_key not in ma_data:
            # Use any available MA deviation
            ma_keys = [k for k in ma_data.keys() if k.endswith('_deviation')]
            if not ma_keys:
                return TradingSignal(SignalType.NO_SIGNAL, 0.0, "No MA deviation data")
            ma_key = ma_keys[0]
        
        deviation = ma_data[ma_key]
        
        if deviation >= self.trend_strength_threshold:
            strength = min(1.0, deviation / self.trend_strength_threshold)
            return TradingSignal(
                SignalType.LONG,
                strength,
                f"Uptrend detected: {deviation:.3f}",
                {'deviation': deviation, 'threshold': self.trend_strength_threshold}
            )
        elif deviation <= -self.trend_strength_threshold:
            strength = min(1.0, abs(deviation) / self.trend_strength_threshold)
            return TradingSignal(
                SignalType.SHORT,
                strength,
                f"Downtrend detected: {deviation:.3f}",
                {'deviation': deviation, 'threshold': self.trend_strength_threshold}
            )
        else:
            return TradingSignal(
                SignalType.NO_SIGNAL,
                0.0,
                f"No clear trend: {deviation:.3f}",
                {'deviation': deviation}
            )

class StrategyManager:
    """Manages multiple trading strategies"""
    
    def __init__(self):
        self.strategies: Dict[str, Strategy] = {}
        self.strategy_weights: Dict[str, float] = {}
        
    def add_strategy(self, name: str, strategy: Strategy, weight: float = 1.0):
        """Add a strategy with optional weight"""
        self.strategies[name] = strategy
        self.strategy_weights[name] = weight
        logger.info(f"Added strategy: {name} (weight: {weight})")
        
    def generate_signals(self, processed_data: Dict[str, Any], 
                        current_position: Dict[str, Any] = None,
                        strategy_names: List[str] = None) -> Dict[str, TradingSignal]:
        """Generate signals from specified strategies"""
        
        if strategy_names is None:
            strategy_names = list(self.strategies.keys())
            
        signals = {}
        for name in strategy_names:
            if name in self.strategies:
                try:
                    signal = self.strategies[name].generate_signal(processed_data, current_position)
                    signals[name] = signal
                    logger.debug(f"Strategy {name}: {signal}")
                except Exception as e:
                    logger.error(f"Error generating signal from strategy {name}: {e}")
                    signals[name] = TradingSignal(SignalType.NO_SIGNAL, 0.0, f"Error: {str(e)}")
            else:
                logger.warning(f"Strategy {name} not found")
                
        return signals
    
    def aggregate_signals(self, signals: Dict[str, TradingSignal]) -> TradingSignal:
        """Aggregate multiple signals into a single signal"""
        
        if not signals:
            return TradingSignal(SignalType.NO_SIGNAL, 0.0, "No signals to aggregate")
        
        # Calculate weighted scores for each signal type
        signal_scores = {
            SignalType.LONG: 0.0,
            SignalType.SHORT: 0.0,
            SignalType.CLOSE_LONG: 0.0,
            SignalType.CLOSE_SHORT: 0.0,
            SignalType.HOLD: 0.0
        }
        
        total_weight = 0.0
        reasons = []
        
        for strategy_name, signal in signals.items():
            weight = self.strategy_weights.get(strategy_name, 1.0)
            
            if signal.signal_type in signal_scores:
                signal_scores[signal.signal_type] += signal.strength * weight
                total_weight += weight
                reasons.append(f"{strategy_name}: {signal.signal_type.value}({signal.strength:.2f})")
        
        if total_weight == 0:
            return TradingSignal(SignalType.NO_SIGNAL, 0.0, "No valid signals")
        
        # Normalize scores
        for signal_type in signal_scores:
            signal_scores[signal_type] /= total_weight
        
        # Find the strongest signal
        max_signal_type = max(signal_scores, key=signal_scores.get)
        max_strength = signal_scores[max_signal_type]
        
        # Only return signal if strength is above threshold
        if max_strength > 0.3:
            return TradingSignal(
                max_signal_type,
                max_strength,
                f"Aggregated signal: {', '.join(reasons)}",
                {'individual_signals': {name: str(signal) for name, signal in signals.items()}}
            )
        else:
            return TradingSignal(
                SignalType.NO_SIGNAL,
                max_strength,
                f"Weak aggregated signal: {', '.join(reasons)}",
                {'individual_signals': {name: str(signal) for name, signal in signals.items()}}
            )
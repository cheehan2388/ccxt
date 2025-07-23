#!/usr/bin/env python3
"""
🎯 Strategy System V3 - Enhanced Flexibility
============================================

V3 Strategy Improvements:
- Dynamic strategy configuration
- Flexible threshold management
- Multiple signal types support
- Enhanced risk management
- Configuration-driven behavior
- All V2 strategies preserved + new flexible ones

Built on strategy_v2.py but with maximum flexibility
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import pandas as pd
import numpy as np

# Import V2 base components
from strategy_v2 import BaseStrategy, StrategySelector, SignalType, TradingSignal

logger = logging.getLogger(__name__)

class StrategyType(Enum):
    """V3 Strategy Types"""
    MEAN_REVERSION = "mean_reversion"
    TREND_FOLLOWING = "trend_following"
    MOMENTUM = "momentum"
    FLEXIBLE = "flexible"
    HYBRID = "hybrid"

class RiskLevel(Enum):
    """Risk Management Levels"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"

@dataclass
class V3StrategyConfig:
    """V3 Strategy Configuration"""
    strategy_type: StrategyType
    thresholds: Dict[str, float]
    risk_level: RiskLevel = RiskLevel.MODERATE
    signal_smoothing: bool = False
    adaptive_thresholds: bool = False
    max_position_size: float = 0.1
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.04
    params: Dict[str, Any] = None

    def __post_init__(self):
        if self.params is None:
            self.params = {}

class FlexibleStrategyV3(BaseStrategy):
    """
    🎯 V3 Flexible Strategy
    
    Adapts to any configuration and feature combination
    """
    
    def __init__(self, config: V3StrategyConfig):
        self.config = config
        self.signal_history = []
        self.adaptive_factor = 1.0
        logger.info(f"Initialized V3 Flexible Strategy ({config.strategy_type.value})")
        self._setup_risk_management()
    
    def _setup_risk_management(self):
        """Setup risk management based on risk level"""
        risk_configs = {
            RiskLevel.CONSERVATIVE: {
                'max_position_size': 0.05,
                'stop_loss_pct': 0.015,
                'take_profit_pct': 0.03,
                'signal_threshold_multiplier': 1.5
            },
            RiskLevel.MODERATE: {
                'max_position_size': 0.1,
                'stop_loss_pct': 0.02,
                'take_profit_pct': 0.04,
                'signal_threshold_multiplier': 1.0
            },
            RiskLevel.AGGRESSIVE: {
                'max_position_size': 0.2,
                'stop_loss_pct': 0.03,
                'take_profit_pct': 0.06,
                'signal_threshold_multiplier': 0.8
            }
        }
        
        if self.config.risk_level in risk_configs:
            risk_config = risk_configs[self.config.risk_level]
            self.config.max_position_size = risk_config['max_position_size']
            self.config.stop_loss_pct = risk_config['stop_loss_pct']
            self.config.take_profit_pct = risk_config['take_profit_pct']
            
            # Adjust thresholds based on risk level
            multiplier = risk_config['signal_threshold_multiplier']
            for key in self.config.thresholds:
                self.config.thresholds[key] *= multiplier
        
        logger.info(f"Risk management setup: {self.config.risk_level.value}")
    
    def get_name(self) -> str:
        return f"V3 Flexible Strategy ({self.config.strategy_type.value})"
    
    def get_required_features(self) -> List[str]:
        return []  # Dynamic feature handling
    
    def generate_signal(self, features: Dict[str, Any], current_position: Dict[str, Any] = None) -> TradingSignal:
        """Generate signal using V3 flexible logic"""
        try:
            if not features.get('valid', False):
                return TradingSignal(SignalType.NO_SIGNAL, 0.0, "Invalid features")
            
            # Get signal value (flexible - can be from any feature engineering)
            signal_value = self._extract_signal_value(features)
            
            # Apply signal smoothing if enabled
            if self.config.signal_smoothing:
                signal_value = self._smooth_signal(signal_value)
            
            # Update adaptive thresholds if enabled
            if self.config.adaptive_thresholds:
                self._update_adaptive_thresholds(signal_value)
            
            # Generate signal based on strategy type
            return self._generate_typed_signal(signal_value, current_position)
            
        except Exception as e:
            logger.error(f"❌ Error generating V3 signal: {e}")
            return TradingSignal(SignalType.NO_SIGNAL, 0.0, f"Error: {str(e)}")
    
    def _extract_signal_value(self, features: Dict[str, Any]) -> float:
        """Extract signal value from features (flexible)"""
        # Try different possible signal sources
        if 'final_signal' in features:
            return features['final_signal']
        elif 'combined_value' in features:
            return features['combined_value']
        elif 'signal' in features:
            return features['signal']
        else:
            # Fallback: use first numeric feature
            for key, value in features.items():
                if isinstance(value, (int, float)) and not np.isnan(value):
                    return value
        
        raise ValueError("No valid signal value found in features")
    
    def _smooth_signal(self, signal_value: float) -> float:
        """Apply signal smoothing"""
        self.signal_history.append(signal_value)
        if len(self.signal_history) > 5:
            self.signal_history.pop(0)
        
        # Simple moving average smoothing
        return np.mean(self.signal_history)
    
    def _update_adaptive_thresholds(self, signal_value: float):
        """Update thresholds based on signal volatility"""
        self.signal_history.append(signal_value)
        if len(self.signal_history) > 20:
            self.signal_history.pop(0)
        
        if len(self.signal_history) >= 10:
            volatility = np.std(self.signal_history)
            # Adjust adaptive factor based on volatility
            self.adaptive_factor = 1.0 + (volatility * 0.5)
            logger.debug(f"Adaptive factor updated: {self.adaptive_factor:.3f}")
    
    def _generate_typed_signal(self, signal_value: float, current_position: Dict[str, Any]) -> TradingSignal:
        """Generate signal based on strategy type"""
        thresholds = self._get_effective_thresholds()
        
        logger.info(f"🎯 V3 Signal Analysis ({self.config.strategy_type.value}):")
        logger.info(f"   Signal Value: {signal_value:.3f}")
        logger.info(f"   Long Threshold: < {thresholds['long']:.3f}")
        logger.info(f"   Short Threshold: > {thresholds['short']:.3f}")
        
        if self.config.strategy_type == StrategyType.MEAN_REVERSION:
            return self._mean_reversion_signal(signal_value, thresholds)
        elif self.config.strategy_type == StrategyType.TREND_FOLLOWING:
            return self._trend_following_signal(signal_value, thresholds)
        elif self.config.strategy_type == StrategyType.MOMENTUM:
            return self._momentum_signal(signal_value, thresholds)
        elif self.config.strategy_type == StrategyType.HYBRID:
            return self._hybrid_signal(signal_value, thresholds, current_position)
        else:  # FLEXIBLE
            return self._flexible_signal(signal_value, thresholds)
    
    def _get_effective_thresholds(self) -> Dict[str, float]:
        """Get thresholds adjusted for adaptive behavior"""
        thresholds = self.config.thresholds.copy()
        
        if self.config.adaptive_thresholds:
            for key in thresholds:
                thresholds[key] *= self.adaptive_factor
        
        return thresholds
    
    def _mean_reversion_signal(self, signal_value: float, thresholds: Dict[str, float]) -> TradingSignal:
        """Mean reversion strategy logic"""
        if signal_value > thresholds['short']:
            # Extreme high values suggest reversion to mean → SHORT
            strength = min(0.9, (signal_value - thresholds['short']) / 2.0 + 0.5)
            reason = f"Mean Reversion: Signal {signal_value:.3f} > {thresholds['short']:.3f} → SHORT"
            logger.info(f"   🔴 SHORT Signal (Mean Reversion, strength: {strength:.2f})")
            return TradingSignal(SignalType.SHORT, strength, reason)
        
        elif signal_value < thresholds['long']:
            # Extreme low values suggest reversion to mean → LONG
            strength = min(0.9, abs(signal_value - thresholds['long']) / 2.0 + 0.5)
            reason = f"Mean Reversion: Signal {signal_value:.3f} < {thresholds['long']:.3f} → LONG"
            logger.info(f"   🟢 LONG Signal (Mean Reversion, strength: {strength:.2f})")
            return TradingSignal(SignalType.LONG, strength, reason)
        
        else:
            reason = f"Mean Reversion: Signal {signal_value:.3f} within range"
            logger.info(f"   ⚪ NO SIGNAL (Mean Reversion)")
            return TradingSignal(SignalType.NO_SIGNAL, 0.0, reason)
    
    def _trend_following_signal(self, signal_value: float, thresholds: Dict[str, float]) -> TradingSignal:
        """Trend following strategy logic"""
        if signal_value > thresholds['short']:
            # High values suggest upward trend → LONG
            strength = min(0.9, (signal_value - thresholds['short']) / 2.0 + 0.5)
            reason = f"Trend Following: Signal {signal_value:.3f} > {thresholds['short']:.3f} → LONG"
            logger.info(f"   🟢 LONG Signal (Trend Following, strength: {strength:.2f})")
            return TradingSignal(SignalType.LONG, strength, reason)
        
        elif signal_value < thresholds['long']:
            # Low values suggest downward trend → SHORT
            strength = min(0.9, abs(signal_value - thresholds['long']) / 2.0 + 0.5)
            reason = f"Trend Following: Signal {signal_value:.3f} < {thresholds['long']:.3f} → SHORT"
            logger.info(f"   🔴 SHORT Signal (Trend Following, strength: {strength:.2f})")
            return TradingSignal(SignalType.SHORT, strength, reason)
        
        else:
            reason = f"Trend Following: Signal {signal_value:.3f} within range"
            logger.info(f"   ⚪ NO SIGNAL (Trend Following)")
            return TradingSignal(SignalType.NO_SIGNAL, 0.0, reason)
    
    def _momentum_signal(self, signal_value: float, thresholds: Dict[str, float]) -> TradingSignal:
        """Momentum strategy logic"""
        # Use tighter thresholds for momentum
        momentum_long = thresholds['long'] * 0.7
        momentum_short = thresholds['short'] * 0.7
        
        if signal_value > momentum_short:
            strength = min(0.9, (signal_value - momentum_short) / 1.5 + 0.6)
            reason = f"Momentum: Signal {signal_value:.3f} > {momentum_short:.3f} → LONG"
            logger.info(f"   🟢 LONG Signal (Momentum, strength: {strength:.2f})")
            return TradingSignal(SignalType.LONG, strength, reason)
        
        elif signal_value < momentum_long:
            strength = min(0.9, abs(signal_value - momentum_long) / 1.5 + 0.6)
            reason = f"Momentum: Signal {signal_value:.3f} < {momentum_long:.3f} → SHORT"
            logger.info(f"   🔴 SHORT Signal (Momentum, strength: {strength:.2f})")
            return TradingSignal(SignalType.SHORT, strength, reason)
        
        else:
            reason = f"Momentum: Signal {signal_value:.3f} within range"
            logger.info(f"   ⚪ NO SIGNAL (Momentum)")
            return TradingSignal(SignalType.NO_SIGNAL, 0.0, reason)
    
    def _hybrid_signal(self, signal_value: float, thresholds: Dict[str, float], current_position: Dict[str, Any]) -> TradingSignal:
        """Hybrid strategy combining multiple approaches"""
        # Use position-aware logic
        position_side = current_position.get('side', 'none') if current_position else 'none'
        
        # Adjust thresholds based on current position
        if position_side == 'long':
            # Make it easier to exit long, harder to enter short
            exit_threshold = thresholds['short'] * 0.8
            enter_threshold = thresholds['long'] * 1.2
        elif position_side == 'short':
            # Make it easier to exit short, harder to enter long
            exit_threshold = thresholds['long'] * 0.8
            enter_threshold = thresholds['short'] * 1.2
        else:
            exit_threshold = 0
            enter_threshold = max(abs(thresholds['long']), abs(thresholds['short']))
        
        if signal_value > thresholds['short']:
            if position_side == 'short':
                # Exit short position
                strength = 0.8
                reason = f"Hybrid: Exit SHORT at {signal_value:.3f}"
                return TradingSignal(SignalType.LONG, strength, reason)
            else:
                # New short entry (mean reversion logic)
                strength = min(0.7, (signal_value - thresholds['short']) / 2.0 + 0.4)
                reason = f"Hybrid: Mean reversion SHORT at {signal_value:.3f}"
                return TradingSignal(SignalType.SHORT, strength, reason)
        
        elif signal_value < thresholds['long']:
            if position_side == 'long':
                # Exit long position
                strength = 0.8
                reason = f"Hybrid: Exit LONG at {signal_value:.3f}"
                return TradingSignal(SignalType.SHORT, strength, reason)
            else:
                # New long entry (mean reversion logic)
                strength = min(0.7, abs(signal_value - thresholds['long']) / 2.0 + 0.4)
                reason = f"Hybrid: Mean reversion LONG at {signal_value:.3f}"
                return TradingSignal(SignalType.LONG, strength, reason)
        
        else:
            reason = f"Hybrid: Signal {signal_value:.3f} within range"
            return TradingSignal(SignalType.NO_SIGNAL, 0.0, reason)
    
    def _flexible_signal(self, signal_value: float, thresholds: Dict[str, float]) -> TradingSignal:
        """Flexible signal generation (user-configurable)"""
        # Default to mean reversion but allow customization via params
        signal_mode = self.config.params.get('signal_mode', 'mean_reversion')
        
        if signal_mode == 'trend_following':
            return self._trend_following_signal(signal_value, thresholds)
        elif signal_mode == 'momentum':
            return self._momentum_signal(signal_value, thresholds)
        else:  # Default mean reversion
            return self._mean_reversion_signal(signal_value, thresholds)

class StrategyManagerV3:
    """
    🎯 V3 Strategy Manager
    
    Enhanced strategy management with flexible configurations
    """
    
    def __init__(self):
        self.strategies = {}
        self.active_strategy = None
        self.strategy_configs = {}
        logger.info("Initialized V3 Strategy Manager")
    
    def add_strategy(self, name: str, strategy: BaseStrategy, config: V3StrategyConfig = None):
        """Add strategy with optional V3 configuration"""
        self.strategies[name] = strategy
        if config:
            self.strategy_configs[name] = config
        logger.info(f"Added V3 strategy: {name}")
    
    def set_active_strategy(self, name: str):
        """Set active strategy"""
        if name not in self.strategies:
            raise ValueError(f"Strategy '{name}' not found")
        self.active_strategy = name
        logger.info(f"Active V3 strategy set to: {name}")
    
    def get_active_strategy(self) -> BaseStrategy:
        """Get active strategy"""
        if not self.active_strategy:
            raise ValueError("No active strategy set")
        return self.strategies[self.active_strategy]
    
    def generate_signal(self, features: Dict[str, Any], current_position: Dict[str, Any] = None) -> TradingSignal:
        """Generate signal using active strategy"""
        if not self.active_strategy:
            return TradingSignal(SignalType.NO_SIGNAL, 0.0, "No active strategy")
        
        strategy = self.strategies[self.active_strategy]
        return strategy.generate_signal(features, current_position)
    
    def list_strategies(self) -> List[str]:
        """List available strategies"""
        return list(self.strategies.keys())
    
    def get_strategy_config(self, name: str) -> Optional[V3StrategyConfig]:
        """Get strategy configuration"""
        return self.strategy_configs.get(name)
    
    def update_strategy_config(self, name: str, config: V3StrategyConfig):
        """Update strategy configuration"""
        if name in self.strategies and isinstance(self.strategies[name], FlexibleStrategyV3):
            self.strategies[name].config = config
            self.strategy_configs[name] = config
            logger.info(f"Updated configuration for strategy: {name}")
        else:
            logger.warning(f"Cannot update config for strategy: {name}")

# V3 Strategy Factory Functions
def create_mean_reversion_v3(thresholds: Dict[str, float], risk_level: RiskLevel = RiskLevel.MODERATE) -> FlexibleStrategyV3:
    """Create V3 mean reversion strategy"""
    config = V3StrategyConfig(
        strategy_type=StrategyType.MEAN_REVERSION,
        thresholds=thresholds,
        risk_level=risk_level,
        signal_smoothing=True
    )
    return FlexibleStrategyV3(config)

def create_trend_following_v3(thresholds: Dict[str, float], risk_level: RiskLevel = RiskLevel.MODERATE) -> FlexibleStrategyV3:
    """Create V3 trend following strategy"""
    config = V3StrategyConfig(
        strategy_type=StrategyType.TREND_FOLLOWING,
        thresholds=thresholds,
        risk_level=risk_level,
        adaptive_thresholds=True
    )
    return FlexibleStrategyV3(config)

def create_hybrid_v3(thresholds: Dict[str, float], risk_level: RiskLevel = RiskLevel.MODERATE) -> FlexibleStrategyV3:
    """Create V3 hybrid strategy"""
    config = V3StrategyConfig(
        strategy_type=StrategyType.HYBRID,
        thresholds=thresholds,
        risk_level=risk_level,
        signal_smoothing=True,
        adaptive_thresholds=True
    )
    return FlexibleStrategyV3(config)

def create_flexible_v3(thresholds: Dict[str, float], params: Dict[str, Any] = None, risk_level: RiskLevel = RiskLevel.MODERATE) -> FlexibleStrategyV3:
    """Create V3 flexible strategy with custom parameters"""
    config = V3StrategyConfig(
        strategy_type=StrategyType.FLEXIBLE,
        thresholds=thresholds,
        risk_level=risk_level,
        params=params or {}
    )
    return FlexibleStrategyV3(config)
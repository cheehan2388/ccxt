#!/usr/bin/env python3
"""
🚀 Trading System V3 Demo - Maximum Flexibility
===============================================

This demo shows your V3 system with maximum flexibility:

Your Example Configuration:
- longshort → zscore preprocessing (30-period)
- open_interest → rolling_minmax preprocessing (30-period)  
- Combination → add + zscore_trend final processing
- Strategy → mean_reversion with your thresholds

Easy to change any configuration without touching code!
"""

import asyncio
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from data_provider import BinanceDataProvider, DataManager
from strategy_v2 import BaseStrategy, StrategySelector, SignalType, TradingSignal
# from trader import Trader  # Will use mock for demo

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PreprocessMethod(Enum):
    """Available preprocessing methods"""
    ZSCORE = "zscore"
    ROLLING_MINMAX = "rolling_minmax"
    ZSCORE_TREND = "zscore_trend"
    ROLLING_STD = "rolling_std"
    MOMENTUM = "momentum"

class CombinationMethod(Enum):
    """Methods to combine features"""
    ADD = "add"
    MULTIPLY = "multiply"
    WEIGHTED_AVG = "weighted_avg"

@dataclass
class FeatureConfig:
    """Configuration for a single feature"""
    name: str
    preprocess: PreprocessMethod
    window: int = 30
    weight: float = 1.0

@dataclass
class CombinationConfig:
    """Configuration for combining features"""
    method: CombinationMethod
    final_preprocess: Optional[PreprocessMethod] = None
    final_window: int = 30

@dataclass
class V3Config:
    """V3 System Configuration - Maximum Flexibility"""
    features: List[FeatureConfig]
    combination: CombinationConfig
    strategy_name: str = "mean_reversion_v1"
    thresholds: Dict[str, float] = field(default_factory=lambda: {"long": -2.5, "short": 2.5})

class V3FlexiblePreprocessor:
    """🧠 V3 Flexible Preprocessor - Handles any preprocessing on any feature"""
    
    def __init__(self):
        logger.info("Initialized V3 Flexible Preprocessor")
    
    def process_feature(self, data: pd.DataFrame, feature_config: FeatureConfig) -> pd.Series:
        """Process a single feature with specified method"""
        feature_name = feature_config.name
        method = feature_config.preprocess
        window = feature_config.window
        
        logger.info(f"🔧 Processing '{feature_name}' with '{method.value}' (window: {window})")
        
        if feature_name not in data.columns:
            raise ValueError(f"Feature '{feature_name}' not found in data")
        
        feature_data = data[feature_name]
        
        if method == PreprocessMethod.ZSCORE:
            return self._zscore(feature_data, window)
        elif method == PreprocessMethod.ROLLING_MINMAX:
            return self._rolling_minmax(feature_data, window)
        elif method == PreprocessMethod.ZSCORE_TREND:
            return self._zscore_trend(feature_data, window)
        elif method == PreprocessMethod.ROLLING_STD:
            return self._rolling_std(feature_data, window)
        elif method == PreprocessMethod.MOMENTUM:
            return self._momentum(feature_data, window)
        else:
            raise ValueError(f"Unknown preprocessing method: {method}")
    
    def _zscore(self, data: pd.Series, window: int) -> pd.Series:
        """Z-score normalization"""
        rolling_mean = data.rolling(window=window, min_periods=window//2).mean()
        rolling_std = data.rolling(window=window, min_periods=window//2).std()
        return (data - rolling_mean) / rolling_std
    
    def _rolling_minmax(self, data: pd.Series, window: int) -> pd.Series:
        """Rolling min-max normalization"""
        rolling_min = data.rolling(window=window, min_periods=window//2).min()
        rolling_max = data.rolling(window=window, min_periods=window//2).max()
        return (data - rolling_min) / (rolling_max - rolling_min)
    
    def _zscore_trend(self, data: pd.Series, window: int) -> pd.Series:
        """Z-score with trend component"""
        zscore = self._zscore(data, window)
        trend = data.diff().rolling(window=window//2, min_periods=window//4).mean()
        trend_zscore = self._zscore(trend, window//2)
        return zscore + 0.3 * trend_zscore
    
    def _rolling_std(self, data: pd.Series, window: int) -> pd.Series:
        """Rolling standard deviation normalization"""
        return data / data.rolling(window=window, min_periods=window//2).std()
    
    def _momentum(self, data: pd.Series, window: int) -> pd.Series:
        """Momentum-based preprocessing"""
        momentum = data.pct_change(window)
        return self._zscore(momentum, window)

class V3FlexibleFeatureEngineer:
    """🔬 V3 Flexible Feature Engineer - Combines any features with any methods"""
    
    def __init__(self, config: V3Config):
        self.config = config
        self.preprocessor = V3FlexiblePreprocessor()
        logger.info(f"Initialized V3 Feature Engineer with {len(config.features)} features")
    
    def engineer_features(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Engineer features according to V3 configuration"""
        try:
            logger.info("🔬 Starting V3 Feature Engineering...")
            
            # Process each feature
            processed_features = {}
            feature_series = {}
            
            for feature_config in self.config.features:
                processed_series = self.preprocessor.process_feature(data, feature_config)
                processed_features[feature_config.name] = processed_series.iloc[-1] if len(processed_series) > 0 else np.nan
                feature_series[feature_config.name] = processed_series
                
                logger.info(f"   ✅ {feature_config.name}: {processed_features[feature_config.name]:.3f}")
            
            # Combine features
            combined_series = self._combine_features(feature_series)
            combined_value = combined_series.iloc[-1] if len(combined_series) > 0 else np.nan
            
            # Apply final preprocessing if specified
            if self.config.combination.final_preprocess:
                logger.info(f"🔄 Applying final preprocessing: {self.config.combination.final_preprocess.value}")
                temp_df = pd.DataFrame({'combined': combined_series})
                final_config = FeatureConfig(
                    name="combined",
                    preprocess=self.config.combination.final_preprocess,
                    window=self.config.combination.final_window
                )
                final_series = self.preprocessor.process_feature(temp_df, final_config)
                final_value = final_series.iloc[-1] if len(final_series) > 0 else np.nan
            else:
                final_series = combined_series
                final_value = combined_value
            
            logger.info(f"🎯 Final Signal: {final_value:.3f}")
            
            return {
                'individual_features': processed_features,
                'combined_value': combined_value,
                'final_signal': final_value,
                'individual_series': feature_series,
                'combined_series': combined_series,
                'final_series': final_series,
                'config': self.config,
                'valid': not np.isnan(final_value)
            }
            
        except Exception as e:
            logger.error(f"❌ Error in feature engineering: {e}")
            return {'valid': False, 'error': str(e)}
    
    def _combine_features(self, feature_series: Dict[str, pd.Series]) -> pd.Series:
        """Combine multiple feature series according to configuration"""
        method = self.config.combination.method
        
        logger.info(f"🔄 Combining features using '{method.value}' method")
        
        series_list = list(feature_series.values())
        if not series_list:
            raise ValueError("No features to combine")
        
        # Align all series to same index
        aligned_series = pd.concat(series_list, axis=1, keys=feature_series.keys())
        aligned_series = aligned_series.dropna()
        
        if method == CombinationMethod.ADD:
            result = aligned_series.sum(axis=1)
        elif method == CombinationMethod.MULTIPLY:
            result = aligned_series.prod(axis=1)
        elif method == CombinationMethod.WEIGHTED_AVG:
            result = aligned_series.mean(axis=1)
        else:
            raise ValueError(f"Unknown combination method: {method}")
        
        return result

class V3FlexibleStrategy(BaseStrategy):
    """🎯 V3 Flexible Strategy - Works with any feature combination"""
    
    def __init__(self, config: V3Config):
        self.config = config
        self.thresholds = config.thresholds
        logger.info(f"Initialized V3 Flexible Strategy (Long: <{self.thresholds['long']}, Short: >{self.thresholds['short']})")
    
    def get_name(self) -> str:
        return f"V3 Flexible Strategy ({self.config.strategy_name})"
    
    def get_required_features(self) -> List[str]:
        return []  # Dynamic feature handling
    
    def generate_signal(self, features: Dict[str, Any], current_position: Dict[str, Any] = None) -> TradingSignal:
        """Generate signal from V3 engineered features"""
        try:
            if not features.get('valid', False):
                return TradingSignal(SignalType.NO_SIGNAL, 0.0, "Invalid features")
            
            signal_value = features['final_signal']
            long_threshold = self.thresholds['long']
            short_threshold = self.thresholds['short']
            
            logger.info(f"🎯 V3 Strategy Analysis:")
            logger.info(f"   Signal Value: {signal_value:.3f}")
            logger.info(f"   Long Threshold: < {long_threshold}")
            logger.info(f"   Short Threshold: > {short_threshold}")
            
            if signal_value > short_threshold:
                strength = min(0.9, (signal_value - short_threshold) / 2.0 + 0.5)
                reason = f"V3 Strategy: Signal {signal_value:.3f} > {short_threshold} → SHORT"
                logger.info(f"   🔴 SHORT Signal Generated (strength: {strength:.2f})")
                return TradingSignal(SignalType.SHORT, strength, reason)
            
            elif signal_value < long_threshold:
                strength = min(0.9, abs(signal_value - long_threshold) / 2.0 + 0.5)
                reason = f"V3 Strategy: Signal {signal_value:.3f} < {long_threshold} → LONG"
                logger.info(f"   🟢 LONG Signal Generated (strength: {strength:.2f})")
                return TradingSignal(SignalType.LONG, strength, reason)
            
            else:
                reason = f"V3 Strategy: Signal {signal_value:.3f} within range [{long_threshold}, {short_threshold}]"
                logger.info(f"   ⚪ NO SIGNAL (within thresholds)")
                return TradingSignal(SignalType.NO_SIGNAL, 0.0, reason)
                
        except Exception as e:
            logger.error(f"❌ Error generating V3 signal: {e}")
            return TradingSignal(SignalType.NO_SIGNAL, 0.0, f"Error: {str(e)}")

class MockTrader:
    """Mock trader for V3 demo"""
    def __init__(self, config):
        self.config = config
        logger.info("Initialized V3 Mock Trader")
    
    async def close(self):
        logger.info("V3 Mock trader closed")

class TradingSystemV3:
    """🚀 Trading System V3 - Maximum Flexibility"""
    
    def __init__(self, config: V3Config):
        self.config = config
        self.data_manager = DataManager()
        self.feature_engineer = V3FlexibleFeatureEngineer(config)
        self.strategy_selector = StrategySelector()
        self.trader = None
        
        self.setup_system()
    
    def setup_system(self):
        """Setup V3 system with flexible configuration"""
        logger.info("🔧 Setting up Trading System V3...")
        
        # 1. Data Provider (from V2)
        binance_provider = BinanceDataProvider()
        self.data_manager.add_provider('binance', binance_provider)
        
        # 2. V3 Flexible Strategy
        flexible_strategy = V3FlexibleStrategy(self.config)
        self.strategy_selector.add_strategy('v3_flexible', flexible_strategy)
        self.strategy_selector.set_active_strategy('v3_flexible')
        
        # 3. Mock Trader
        self.trader = MockTrader({})
        
        logger.info("✅ V3 System setup complete!")
        self._log_configuration()
    
    def _log_configuration(self):
        """Log the current V3 configuration"""
        logger.info("📋 V3 Configuration:")
        for i, feature in enumerate(self.config.features):
            logger.info(f"   Feature {i+1}: {feature.name} → {feature.preprocess.value} (window: {feature.window})")
        logger.info(f"   Combination: {self.config.combination.method.value}")
        if self.config.combination.final_preprocess:
            logger.info(f"   Final Processing: {self.config.combination.final_preprocess.value}")
        logger.info(f"   Strategy: {self.config.strategy_name}")
        logger.info(f"   Thresholds: LONG < {self.config.thresholds['long']}, SHORT > {self.config.thresholds['short']}")
    
    async def generate_demo_data(self) -> pd.DataFrame:
        """Generate demo data with multiple features"""
        logger.info("📊 Generating V3 demo data...")
        
        dates = pd.date_range(start=datetime.now() - timedelta(days=5), periods=100, freq='1h')
        
        # Generate realistic patterns
        base_price = 45000
        price_changes = np.cumsum(np.random.randn(100) * 50)
        
        demo_data = pd.DataFrame({
            'open': base_price + price_changes,
            'high': base_price + price_changes + np.abs(np.random.randn(100) * 50),
            'low': base_price + price_changes - np.abs(np.random.randn(100) * 50),
            'close': base_price + price_changes + np.random.randn(100) * 30,
            'volume': np.random.lognormal(6, 0.5, 100),
            'open_interest': 1000000 + np.cumsum(np.random.randn(100) * 10000),
            'longshort': np.cumsum(np.random.randn(100) * 0.1),  # Long/short ratio
            'funding_rate': np.random.randn(100) * 0.001,
        }, index=dates)
        
        logger.info(f"✅ Generated {len(demo_data)} data points with features: {list(demo_data.columns)}")
        return demo_data
    
    async def run_trading_cycle(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Run V3 trading cycle"""
        logger.info(f"\n{'='*80}")
        logger.info("🚀 RUNNING V3 TRADING CYCLE")
        logger.info(f"{'='*80}")
        
        try:
            # 1. V3 Feature Engineering
            logger.info("\n🔬 Step 1: V3 Feature Engineering")
            features = self.feature_engineer.engineer_features(data)
            
            # 2. V3 Signal Generation
            logger.info("\n🎯 Step 2: V3 Signal Generation")
            mock_position = {'symbol': 'BTC/USDT', 'side': 'none', 'size': 0.0, 'entry_price': 0.0}
            signal = self.strategy_selector.generate_signal(features, mock_position)
            
            # 3. V3 Trade Execution
            logger.info("\n💰 Step 3: V3 Trade Execution")
            trade_result = await self._execute_trade(signal, mock_position)
            
            return {
                'features': features,
                'signal': signal,
                'trade_result': trade_result,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"❌ Error in V3 trading cycle: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _execute_trade(self, signal: TradingSignal, current_position: Dict) -> Dict[str, Any]:
        """Execute trade with V3 logic"""
        current_price = 45000
        position_size = 0.01
        
        logger.info(f"💼 V3 Trade Execution:")
        logger.info(f"   Signal: {signal.signal_type.value} (strength: {signal.strength:.2f})")
        logger.info(f"   Reason: {signal.reason}")
        
        if signal.signal_type == SignalType.LONG:
            if current_position['side'] == 'none':
                action = "🟢 OPEN LONG POSITION"
                new_position = {'side': 'long', 'size': position_size, 'entry_price': current_price}
            elif current_position['side'] == 'short':
                action = "🔄 CLOSE SHORT + OPEN LONG"
                new_position = {'side': 'long', 'size': position_size, 'entry_price': current_price}
            else:
                action = "😴 HOLD LONG POSITION"
                new_position = current_position.copy()
        
        elif signal.signal_type == SignalType.SHORT:
            if current_position['side'] == 'none':
                action = "🔴 OPEN SHORT POSITION"
                new_position = {'side': 'short', 'size': position_size, 'entry_price': current_price}
            elif current_position['side'] == 'long':
                action = "🔄 CLOSE LONG + OPEN SHORT"
                new_position = {'side': 'short', 'size': position_size, 'entry_price': current_price}
            else:
                action = "😴 HOLD SHORT POSITION"
                new_position = current_position.copy()
        else:
            action = "⏸️ NO ACTION"
            new_position = current_position.copy()
        
        logger.info(f"   🎯 Action: {action}")
        
        return {
            'action': action,
            'current_position': current_position,
            'new_position': new_position,
            'signal': signal
        }
    
    async def run_demo(self):
        """Run V3 demo"""
        logger.info("🚀 STARTING V3 DEMO")
        logger.info("=" * 50)
        
        try:
            demo_data = await self.generate_demo_data()
            result = await self.run_trading_cycle(demo_data)
            
            if result['success']:
                await self._print_results(result, demo_data)
            else:
                logger.error(f"❌ Demo failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ V3 Demo failed: {e}")
        finally:
            await self._cleanup()
    
    async def _print_results(self, result: Dict, data: pd.DataFrame):
        """Print V3 results"""
        logger.info(f"\n{'='*80}")
        logger.info("🎉 V3 DEMO RESULTS - MAXIMUM FLEXIBILITY ACHIEVED")
        logger.info(f"{'='*80}")
        
        features = result['features']
        signal = result['signal']
        trade_result = result['trade_result']
        
        # Show feature engineering results
        logger.info(f"\n🔬 V3 FEATURE ENGINEERING RESULTS:")
        if 'individual_features' in features:
            for name, value in features['individual_features'].items():
                logger.info(f"   ✅ {name}: {value:.3f}")
        logger.info(f"   ✅ Combined: {features.get('combined_value', 'N/A'):.3f}")
        logger.info(f"   ✅ Final Signal: {features.get('final_signal', 'N/A'):.3f}")
        
        # Show strategy results
        logger.info(f"\n🎯 V3 STRATEGY RESULTS:")
        logger.info(f"   ✅ Signal: {signal.signal_type.value}")
        logger.info(f"   ✅ Strength: {signal.strength:.2f}")
        logger.info(f"   ✅ Reason: {signal.reason}")
        
        # Show trade results
        logger.info(f"\n💰 V3 TRADE RESULTS:")
        logger.info(f"   ✅ Action: {trade_result['action']}")
        logger.info(f"   ✅ Position: {trade_result['current_position']['side']} → {trade_result['new_position']['side']}")
        
        logger.info(f"\n🎉 V3 SUCCESS - MAXIMUM FLEXIBILITY ACHIEVED!")
        logger.info(f"   🔧 Easy configuration changes - no code modifications needed")
        logger.info(f"   📊 Any feature + any preprocessing + any combination")
        logger.info(f"   🎯 All V2 strategies preserved + new flexible ones")
        logger.info(f"   🚀 Future-ready for any data types")
    
    async def _cleanup(self):
        """Cleanup V3 system"""
        if self.trader:
            await self.trader.close()

# Configuration Examples
def create_your_example_config() -> V3Config:
    """Your exact example: zscore longshort + rolling_minmax open_interest + zscore_trend final"""
    return V3Config(
        features=[
            FeatureConfig(name="longshort", preprocess=PreprocessMethod.ZSCORE, window=30),
            FeatureConfig(name="open_interest", preprocess=PreprocessMethod.ROLLING_MINMAX, window=30)
        ],
        combination=CombinationConfig(
            method=CombinationMethod.ADD,
            final_preprocess=PreprocessMethod.ZSCORE_TREND,
            final_window=30
        ),
        strategy_name="mean_reversion_v1",
        thresholds={"long": -2.5, "short": 2.5}
    )

def create_alternative_config() -> V3Config:
    """Alternative configuration to show flexibility"""
    return V3Config(
        features=[
            FeatureConfig(name="volume", preprocess=PreprocessMethod.MOMENTUM, window=20),
            FeatureConfig(name="open_interest", preprocess=PreprocessMethod.ZSCORE, window=25),
            FeatureConfig(name="longshort", preprocess=PreprocessMethod.ROLLING_STD, window=15)
        ],
        combination=CombinationConfig(
            method=CombinationMethod.MULTIPLY,
            final_preprocess=PreprocessMethod.ROLLING_MINMAX,
            final_window=20
        ),
        strategy_name="trend_following_v1",
        thresholds={"long": -1.8, "short": 1.8}
    )

async def main():
    """Main V3 demo function"""
    print("🚀 TRADING SYSTEM V3 - MAXIMUM FLEXIBILITY DEMO")
    print("=" * 65)
    print("\nV3 Revolutionary Features:")
    print("• 🎯 Smart configuration system - no more hardcoded names")
    print("• 🔧 Flexible preprocessing combinations (zscore, rolling_minmax, etc.)")
    print("• 🔬 Easy feature mixing (any combination of features)")
    print("• 🎛️ All V2 choices preserved but more flexible")
    print("• 🚀 Future-ready for any data types")
    print("\nYour Exact Example Configuration:")
    print("• ✅ longshort → zscore preprocessing (30-period)")
    print("• ✅ open_interest → rolling_minmax preprocessing (30-period)")
    print("• ✅ combination → add + zscore_trend final processing")
    print("• ✅ strategy → mean_reversion with your thresholds (-2.5, +2.5)")
    print("\n🚀 Starting V3 demo with your configuration...\n")
    
    # Use your exact configuration
    config = create_your_example_config()
    
    # Create and run V3 system
    v3_system = TradingSystemV3(config)
    await v3_system.run_demo()
    
    print(f"\n🎉 V3 Demo Complete!")
    print("✨ Now you can easily change ANY configuration without touching code!")
    print("🔧 Just modify the config object - maximum flexibility achieved!")

if __name__ == "__main__":
    asyncio.run(main())
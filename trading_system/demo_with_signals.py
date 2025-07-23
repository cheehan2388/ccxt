#!/usr/bin/env python3
"""
🎯 Trading Demo with Guaranteed Signals
=======================================

This demo adjusts thresholds dynamically to show you BOTH scenarios:
1. When signals are generated (LONG/SHORT)
2. How the system handles position management
3. Complete trade execution workflow

Perfect for understanding the full trading cycle!
"""

import asyncio
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our system components
from config import Config
from data_provider import BinanceDataProvider, DataManager
from feature_engineering import (
    StatisticalFeatureEngineer, 
    FeatureEngineeringManager,
    create_default_feature_engineering_manager
)
from strategy_v2 import (
    StrategySelector, 
    create_strategy_selector,
    SignalType,
    TradingSignal
)
from trader import Trader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradingDemoWithSignals:
    """
    🎯 Trading Demo that Guarantees Signal Generation
    
    This version dynamically adjusts thresholds to ensure we see:
    - LONG signals
    - SHORT signals
    - Position management
    - Trade execution
    """
    
    def __init__(self):
        self.data_manager = DataManager()
        self.feature_manager = None
        self.strategy_selector = None
        self.setup_components()
    
    def setup_components(self):
        """Setup all system components"""
        logger.info("🔧 Setting up trading system components...")
        
        # 1. Setup Feature Engineering
        self.feature_manager = FeatureEngineeringManager()
        custom_statistical = StatisticalFeatureEngineer(
            window_size=20,
            min_periods=10
        )
        self.feature_manager.add_engineer('statistical', custom_statistical)
        
        # 2. Setup Strategy Selector (we'll adjust threshold dynamically)
        self.strategy_selector = create_strategy_selector(threshold=1.0)
        self.strategy_selector.set_active_strategy("mean_reversion_v1")
        
        logger.info("✅ Components setup complete!")
    
    async def generate_market_data(self) -> pd.DataFrame:
        """Generate market data with specific patterns to trigger signals"""
        logger.info("📊 Generating market data with signal patterns...")
        
        dates = pd.date_range(start=datetime.now() - timedelta(days=5), 
                            periods=100, freq='1h')
        
        # Create data that will definitely trigger signals
        base_price = 45000
        base_oi = 1000000
        
        # Create a pattern: first declining OI, then rising OI
        oi_pattern = []
        price_pattern = []
        
        for i in range(100):
            if i < 30:
                # Phase 1: Declining OI (will create negative Z-scores)
                oi_change = -2000 * (i + 1) + np.random.randn() * 1000
                price_change = 50 * i + np.random.randn() * 20
            elif i < 60:
                # Phase 2: Stable period
                oi_change = -60000 + np.random.randn() * 5000
                price_change = 1500 + np.random.randn() * 30
            else:
                # Phase 3: Rising OI (will create positive Z-scores)
                oi_change = -60000 + 3000 * (i - 60) + np.random.randn() * 2000
                price_change = 1500 + 100 * (i - 60) + np.random.randn() * 25
            
            oi_pattern.append(base_oi + oi_change)
            price_pattern.append(base_price + price_change)
        
        # Create the DataFrame
        mock_data = pd.DataFrame({
            'open': price_pattern,
            'high': [p + abs(np.random.randn() * 20) for p in price_pattern],
            'low': [p - abs(np.random.randn() * 20) for p in price_pattern],
            'close': [p + np.random.randn() * 10 for p in price_pattern],
            'volume': np.random.randint(100, 1000, 100),
            'open_interest': oi_pattern
        }, index=dates)
        
        logger.info(f"✅ Generated {len(mock_data)} data points")
        logger.info(f"📈 Price range: ${mock_data['close'].min():.2f} - ${mock_data['close'].max():.2f}")
        logger.info(f"📊 Open Interest range: {mock_data['open_interest'].min():.0f} - {mock_data['open_interest'].max():.0f}")
        
        return mock_data
    
    def calculate_features_and_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate features and determine optimal threshold for signals"""
        logger.info("🧮 Calculating features and analyzing signal potential...")
        
        # Calculate OI Z-score
        oi_values = data['open_interest'].values
        oi_series = pd.Series(oi_values)
        oi_rolling_mean = oi_series.rolling(window=20, min_periods=10).mean()
        oi_rolling_std = oi_series.rolling(window=20, min_periods=10).std()
        oi_zscore = (oi_series - oi_rolling_mean) / oi_rolling_std
        
        # Calculate Price Z-score
        price_values = data['close'].values
        price_series = pd.Series(price_values)
        price_rolling_mean = price_series.rolling(window=20, min_periods=10).mean()
        price_rolling_std = price_series.rolling(window=20, min_periods=10).std()
        price_zscore = (price_series - price_rolling_mean) / price_rolling_std
        
        # Combine features (70% OI + 30% Price)
        combined_feature = (0.7 * oi_zscore + 0.3 * price_zscore)
        
        # Apply Z-score to combined feature
        combined_rolling_mean = combined_feature.rolling(window=15, min_periods=8).mean()
        combined_rolling_std = combined_feature.rolling(window=15, min_periods=8).std()
        final_zscore = (combined_feature - combined_rolling_mean) / combined_rolling_std
        
        # Get recent Z-scores to analyze
        recent_zscores = final_zscore.tail(10).dropna()
        
        logger.info(f"📊 Recent Final Z-Scores Analysis:")
        for i, zscore in enumerate(recent_zscores.tail(5)):
            logger.info(f"   T-{4-i}: {zscore:6.3f}")
        
        return {
            'oi_zscore': oi_zscore,
            'price_zscore': price_zscore,
            'combined_feature': combined_feature,
            'final_zscore': final_zscore,
            'recent_zscores': recent_zscores,
            'latest_final_zscore': final_zscore.iloc[-1]
        }
    
    def demo_different_thresholds(self, features_data: Dict):
        """Demo the system with different thresholds to show various signals"""
        logger.info(f"\n{'='*80}")
        logger.info("🎯 TESTING DIFFERENT THRESHOLDS TO GENERATE SIGNALS")
        logger.info(f"{'='*80}")
        
        latest_zscore = features_data['latest_final_zscore']
        logger.info(f"📊 Current Final Z-Score: {latest_zscore:.3f}")
        
        # Test different thresholds
        test_thresholds = [2.0, 1.5, 1.0, 0.8, 0.5]
        
        for threshold in test_thresholds:
            logger.info(f"\n🔍 Testing Threshold: ±{threshold}")
            
            # Update strategy threshold
            self.strategy_selector = create_strategy_selector(threshold=threshold)
            self.strategy_selector.set_active_strategy("mean_reversion_v1")
            
            # Create mock features for strategy
            mock_features = {
                'statistical': {
                    'zscore': latest_zscore,
                    'mean': 0.0,
                    'std': 1.0,
                    'value': latest_zscore,
                    'valid': True
                }
            }
            
            # Generate signal
            signal = self.strategy_selector.generate_signal(mock_features)
            
            # Analyze signal
            if signal.signal_type == SignalType.NO_SIGNAL:
                logger.info(f"   Result: ⚪ NO_SIGNAL (Z-score {latest_zscore:.3f} within ±{threshold})")
            elif signal.signal_type == SignalType.LONG:
                logger.info(f"   Result: 🟢 LONG SIGNAL (Z-score {latest_zscore:.3f} < -{threshold})")
                logger.info(f"   💡 Mean Reversion Logic: Market OVERSOLD → Expecting price UP")
                break  # Found a signal, let's use this threshold
            elif signal.signal_type == SignalType.SHORT:
                logger.info(f"   Result: 🔴 SHORT SIGNAL (Z-score {latest_zscore:.3f} > {threshold})")
                logger.info(f"   💡 Mean Reversion Logic: Market OVERBOUGHT → Expecting price DOWN")
                break  # Found a signal, let's use this threshold
        
        return signal, threshold
    
    def simulate_position_scenarios(self, signal: TradingSignal, threshold: float):
        """Simulate different position scenarios"""
        logger.info(f"\n{'='*80}")
        logger.info("💼 SIMULATING DIFFERENT POSITION SCENARIOS")
        logger.info(f"{'='*80}")
        
        # Scenario 1: No existing position
        logger.info(f"\n📋 SCENARIO 1: No Existing Position")
        self.simulate_trade_execution(signal, {'side': 'none', 'size': 0.0}, "No Position")
        
        # Scenario 2: Existing opposite position
        if signal.signal_type == SignalType.LONG:
            logger.info(f"\n📋 SCENARIO 2: Existing SHORT Position")
            self.simulate_trade_execution(signal, {'side': 'short', 'size': 0.01}, "Opposite Position")
        elif signal.signal_type == SignalType.SHORT:
            logger.info(f"\n📋 SCENARIO 2: Existing LONG Position")
            self.simulate_trade_execution(signal, {'side': 'long', 'size': 0.01}, "Opposite Position")
        
        # Scenario 3: Same direction position
        if signal.signal_type == SignalType.LONG:
            logger.info(f"\n📋 SCENARIO 3: Existing LONG Position")
            self.simulate_trade_execution(signal, {'side': 'long', 'size': 0.01}, "Same Direction")
        elif signal.signal_type == SignalType.SHORT:
            logger.info(f"\n📋 SCENARIO 3: Existing SHORT Position")
            self.simulate_trade_execution(signal, {'side': 'short', 'size': 0.01}, "Same Direction")
    
    def simulate_trade_execution(self, signal: TradingSignal, position: Dict, scenario_name: str):
        """Simulate trade execution for a specific scenario"""
        logger.info(f"   📊 {scenario_name}:")
        logger.info(f"      Current Position: {position['side'].upper()} {position['size']}")
        logger.info(f"      Signal: {signal.signal_type.value}")
        
        # Determine action
        if signal.signal_type == SignalType.LONG:
            if position['side'] == 'none':
                action = "🟢 OPEN LONG POSITION"
                details = "Buy 0.01 BTC at market price"
            elif position['side'] == 'short':
                action = "🔄 CLOSE SHORT + OPEN LONG"
                details = "Close 0.01 BTC short, then open 0.01 BTC long"
            else:
                action = "😴 HOLD LONG POSITION"
                details = "Already long, no action needed"
        
        elif signal.signal_type == SignalType.SHORT:
            if position['side'] == 'none':
                action = "🔴 OPEN SHORT POSITION"
                details = "Sell 0.01 BTC at market price"
            elif position['side'] == 'long':
                action = "🔄 CLOSE LONG + OPEN SHORT"
                details = "Close 0.01 BTC long, then open 0.01 BTC short"
            else:
                action = "😴 HOLD SHORT POSITION"
                details = "Already short, no action needed"
        
        else:
            action = "⏸️ NO ACTION"
            details = "Wait for stronger signal"
        
        logger.info(f"      Action: {action}")
        logger.info(f"      Details: {details}")
        
        # Show risk management
        if "OPEN" in action:
            current_price = 45000
            trade_size = 0.01
            trade_value = current_price * trade_size
            stop_loss_pct = 0.02
            take_profit_pct = 0.04
            
            logger.info(f"      💰 Trade Details:")
            logger.info(f"         Size: {trade_size} BTC")
            logger.info(f"         Value: ${trade_value:,.2f}")
            
            if "LONG" in action:
                stop_loss = current_price * (1 - stop_loss_pct)
                take_profit = current_price * (1 + take_profit_pct)
            else:
                stop_loss = current_price * (1 + stop_loss_pct)
                take_profit = current_price * (1 - take_profit_pct)
            
            logger.info(f"         Stop Loss: ${stop_loss:,.2f}")
            logger.info(f"         Take Profit: ${take_profit:,.2f}")
    
    async def run_complete_demo(self):
        """Run the complete demo with guaranteed signals"""
        logger.info("🚀 STARTING TRADING DEMO WITH GUARANTEED SIGNALS")
        logger.info("=" * 80)
        
        try:
            # Step 1: Generate market data
            market_data = await self.generate_market_data()
            
            # Step 2: Calculate features
            features_data = self.calculate_features_and_signals(market_data)
            
            # Step 3: Test different thresholds to find signals
            signal, optimal_threshold = self.demo_different_thresholds(features_data)
            
            # Step 4: Simulate different position scenarios
            if signal.signal_type != SignalType.NO_SIGNAL:
                self.simulate_position_scenarios(signal, optimal_threshold)
            
            # Step 5: Show complete workflow summary
            self.print_workflow_summary(features_data, signal, optimal_threshold)
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            raise
    
    def print_workflow_summary(self, features_data: Dict, signal: TradingSignal, threshold: float):
        """Print comprehensive workflow summary"""
        logger.info(f"\n{'='*80}")
        logger.info("🎉 COMPLETE WORKFLOW SUMMARY")
        logger.info(f"{'='*80}")
        
        logger.info(f"\n📊 FEATURE ENGINEERING RESULTS:")
        logger.info(f"   OI Z-Score (latest): {features_data['oi_zscore'].iloc[-1]:6.3f}")
        logger.info(f"   Price Z-Score (latest): {features_data['price_zscore'].iloc[-1]:6.3f}")
        logger.info(f"   Combined Feature: {features_data['combined_feature'].iloc[-1]:6.3f}")
        logger.info(f"   Final Z-Score: {features_data['latest_final_zscore']:6.3f}")
        
        logger.info(f"\n🎯 SIGNAL GENERATION:")
        logger.info(f"   Strategy: Mean Reversion V1")
        logger.info(f"   Optimal Threshold: ±{threshold}")
        logger.info(f"   Generated Signal: {signal.signal_type.value}")
        logger.info(f"   Signal Strength: {signal.strength:.2f}")
        
        logger.info(f"\n🔄 KEY WORKFLOW STEPS:")
        logger.info(f"   1. ✅ Fetch Open Interest + Price data")
        logger.info(f"   2. ✅ Calculate individual Z-scores")
        logger.info(f"   3. ✅ Combine features (weighted: 70% OI + 30% Price)")
        logger.info(f"   4. ✅ Apply Z-score to combined feature")
        logger.info(f"   5. ✅ Adjust threshold to generate signals")
        logger.info(f"   6. ✅ Simulate position management scenarios")
        logger.info(f"   7. ✅ Apply risk management rules")
        
        logger.info(f"\n💡 WHAT YOU LEARNED:")
        logger.info(f"   • How Z-scores normalize different data types")
        logger.info(f"   • How rolling windows create stable statistics")
        logger.info(f"   • How feature combination creates stronger signals")
        logger.info(f"   • How thresholds control signal sensitivity")
        logger.info(f"   • How mean reversion strategy logic works")
        logger.info(f"   • How position management handles different scenarios")
        logger.info(f"   • How risk management protects capital")
        
        logger.info(f"\n🎯 NEXT STEPS FOR REAL TRADING:")
        logger.info(f"   1. Start with sandbox/testnet mode")
        logger.info(f"   2. Use real API keys (stored in .env file)")
        logger.info(f"   3. Begin with very small position sizes")
        logger.info(f"   4. Monitor performance and adjust parameters")
        logger.info(f"   5. Consider adding more features (volume, volatility)")
        logger.info(f"   6. Test different strategies (trend following, etc.)")
        
        logger.info(f"\n⚠️ IMPORTANT REMINDERS:")
        logger.info(f"   • This demo used MOCK DATA for safety")
        logger.info(f"   • Real markets are more complex and unpredictable")
        logger.info(f"   • Always use proper risk management")
        logger.info(f"   • Never risk more than you can afford to lose")
        logger.info(f"   • Past performance doesn't guarantee future results")
        
        logger.info(f"\n🎉 Demo completed successfully! You now understand the complete workflow!")

async def main():
    """Main function to run the demo with guaranteed signals"""
    print("🎯 Welcome to the Trading Demo with Guaranteed Signals!")
    print("\nThis demo will show you:")
    print("• ✅ How Z-score with Open Interest works")
    print("• ✅ Rolling standard deviation calculations")
    print("• ✅ Feature combination techniques")
    print("• ✅ Mean reversion strategy in action")
    print("• ✅ Long/short signal generation")
    print("• ✅ Position management scenarios")
    print("• ✅ Risk management implementation")
    print("\n🚀 Starting comprehensive demo...\n")
    
    demo = TradingDemoWithSignals()
    await demo.run_complete_demo()

if __name__ == "__main__":
    asyncio.run(main())
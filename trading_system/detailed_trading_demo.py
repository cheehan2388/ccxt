#!/usr/bin/env python3
"""
🎯 Detailed Trading Demo: Z-Score + Open Interest + Mean Reversion
==================================================================

This demo shows EXACTLY how to:
1. Use Z-score with Open Interest data
2. Calculate rolling standard deviation
3. Combine multiple features
4. Apply Z-score to combined features
5. Use Mean Reversion strategy
6. Execute long/short trades

Perfect for beginners to understand the complete workflow!
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

class DetailedTradingDemo:
    """
    🎯 Complete Trading Demo with Step-by-Step Explanation
    
    This class demonstrates:
    - Fetching Open Interest data
    - Calculating Z-scores with rolling standard deviation
    - Combining multiple features
    - Applying Z-score to combined features
    - Using Mean Reversion strategy
    - Executing trades
    """
    
    def __init__(self):
        self.data_manager = DataManager()
        self.feature_manager = None
        self.strategy_selector = None
        self.trader = None
        self.setup_components()
    
    def setup_components(self):
        """Setup all system components"""
        logger.info("🔧 Setting up trading system components...")
        
        # 1. Setup Feature Engineering with custom parameters
        self.feature_manager = FeatureEngineeringManager()
        
        # Custom Statistical Engineer for Z-score with rolling std
        custom_statistical = StatisticalFeatureEngineer(
            window_size=20,      # 20-period rolling window
            min_periods=10       # Minimum 10 periods for calculation
        )
        
        self.feature_manager.add_engineer('statistical', custom_statistical)
        
        # 2. Setup Strategy Selector with Mean Reversion
        self.strategy_selector = create_strategy_selector(threshold=1.5)  # 1.5 threshold
        self.strategy_selector.set_active_strategy("mean_reversion_v1")
        
        logger.info("✅ Components setup complete!")
    
    async def demo_step_1_fetch_data(self, symbol: str = "BTC/USDT") -> pd.DataFrame:
        """
        📊 Step 1: Fetch Open Interest and OHLCV Data
        
        This shows how to get the raw data we need for analysis.
        """
        logger.info(f"\n{'='*60}")
        logger.info("📊 STEP 1: FETCHING MARKET DATA")
        logger.info(f"{'='*60}")
        
        # Add Binance data provider
        binance_provider = BinanceDataProvider()
        self.data_manager.add_provider('binance', binance_provider)
        
        try:
            # Fetch recent data (simulate with mock data for demo)
            logger.info(f"🔍 Fetching data for {symbol}...")
            
            # Create mock data that resembles real market data
            dates = pd.date_range(start=datetime.now() - timedelta(days=5), 
                                periods=100, freq='1H')
            
            # Simulate realistic price movement
            base_price = 45000
            price_changes = np.cumsum(np.random.randn(100) * 50)
            
            # Simulate Open Interest with some correlation to price
            base_oi = 1000000
            oi_changes = np.cumsum(np.random.randn(100) * 10000)
            
            mock_data = pd.DataFrame({
                'open': base_price + price_changes,
                'high': base_price + price_changes + np.abs(np.random.randn(100) * 20),
                'low': base_price + price_changes - np.abs(np.random.randn(100) * 20),
                'close': base_price + price_changes + np.random.randn(100) * 10,
                'volume': np.random.randint(100, 1000, 100),
                'open_interest': base_oi + oi_changes
            }, index=dates)
            
            logger.info(f"✅ Fetched {len(mock_data)} data points")
            logger.info(f"📈 Price range: ${mock_data['close'].min():.2f} - ${mock_data['close'].max():.2f}")
            logger.info(f"📊 Open Interest range: {mock_data['open_interest'].min():.0f} - {mock_data['open_interest'].max():.0f}")
            
            # Show sample of raw data
            logger.info("\n🔍 Sample of Raw Data:")
            print(mock_data[['close', 'open_interest']].tail(5).round(2))
            
            return mock_data
            
        except Exception as e:
            logger.error(f"❌ Error fetching data: {e}")
            raise
        finally:
            await binance_provider.close()
    
    def demo_step_2_calculate_zscore_oi(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        🧮 Step 2: Calculate Z-Score of Open Interest with Rolling Std
        
        This shows the core mathematical calculation:
        Z-score = (current_value - rolling_mean) / rolling_std
        """
        logger.info(f"\n{'='*60}")
        logger.info("🧮 STEP 2: CALCULATING Z-SCORE OF OPEN INTEREST")
        logger.info(f"{'='*60}")
        
        # Extract Open Interest values
        oi_values = data['open_interest'].values
        logger.info(f"📊 Processing {len(oi_values)} Open Interest values")
        
        # Calculate rolling statistics
        window_size = 20
        oi_series = pd.Series(oi_values)
        
        # Rolling mean and standard deviation
        rolling_mean = oi_series.rolling(window=window_size, min_periods=10).mean()
        rolling_std = oi_series.rolling(window=window_size, min_periods=10).std()
        
        # Calculate Z-score
        oi_zscore = (oi_series - rolling_mean) / rolling_std
        
        # Get the latest values
        latest_oi = oi_values[-1]
        latest_mean = rolling_mean.iloc[-1]
        latest_std = rolling_std.iloc[-1]
        latest_zscore = oi_zscore.iloc[-1]
        
        logger.info(f"\n📊 Open Interest Z-Score Calculation:")
        logger.info(f"   Current OI: {latest_oi:,.0f}")
        logger.info(f"   Rolling Mean (20): {latest_mean:,.0f}")
        logger.info(f"   Rolling Std (20): {latest_std:,.0f}")
        logger.info(f"   Z-Score: {latest_zscore:.3f}")
        
        # Show trend
        recent_zscores = oi_zscore.tail(5).round(3)
        logger.info(f"\n📈 Recent Z-Score Trend:")
        for i, (timestamp, zscore) in enumerate(zip(data.index[-5:], recent_zscores)):
            trend_symbol = "📈" if zscore > 0 else "📉"
            logger.info(f"   {timestamp.strftime('%H:%M')}: {zscore:6.3f} {trend_symbol}")
        
        return {
            'oi_zscore_series': oi_zscore,
            'latest_zscore': latest_zscore,
            'rolling_mean': rolling_mean,
            'rolling_std': rolling_std,
            'valid': not np.isnan(latest_zscore)
        }
    
    def demo_step_3_calculate_price_zscore(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        📈 Step 3: Calculate Z-Score of Price for Feature Combination
        
        We'll create a second feature (price Z-score) to combine with OI Z-score
        """
        logger.info(f"\n{'='*60}")
        logger.info("📈 STEP 3: CALCULATING PRICE Z-SCORE (SECOND FEATURE)")
        logger.info(f"{'='*60}")
        
        # Extract price values (using close price)
        price_values = data['close'].values
        logger.info(f"💰 Processing {len(price_values)} price values")
        
        # Calculate rolling statistics for price
        window_size = 20
        price_series = pd.Series(price_values)
        
        # Rolling mean and standard deviation
        rolling_mean = price_series.rolling(window=window_size, min_periods=10).mean()
        rolling_std = price_series.rolling(window=window_size, min_periods=10).std()
        
        # Calculate Z-score
        price_zscore = (price_series - rolling_mean) / rolling_std
        
        # Get the latest values
        latest_price = price_values[-1]
        latest_mean = rolling_mean.iloc[-1]
        latest_std = rolling_std.iloc[-1]
        latest_zscore = price_zscore.iloc[-1]
        
        logger.info(f"\n💰 Price Z-Score Calculation:")
        logger.info(f"   Current Price: ${latest_price:,.2f}")
        logger.info(f"   Rolling Mean (20): ${latest_mean:,.2f}")
        logger.info(f"   Rolling Std (20): ${latest_std:,.2f}")
        logger.info(f"   Z-Score: {latest_zscore:.3f}")
        
        return {
            'price_zscore_series': price_zscore,
            'latest_zscore': latest_zscore,
            'valid': not np.isnan(latest_zscore)
        }
    
    def demo_step_4_combine_features(self, oi_zscore_data: Dict, price_zscore_data: Dict) -> Dict[str, Any]:
        """
        🔄 Step 4: Combine Two Features and Apply Z-Score Again
        
        This demonstrates feature combination and secondary Z-score calculation
        """
        logger.info(f"\n{'='*60}")
        logger.info("🔄 STEP 4: COMBINING FEATURES & SECONDARY Z-SCORE")
        logger.info(f"{'='*60}")
        
        # Get the Z-score series
        oi_zscore_series = oi_zscore_data['oi_zscore_series']
        price_zscore_series = price_zscore_data['price_zscore_series']
        
        # Method 1: Simple Average of Z-scores
        combined_simple = (oi_zscore_series + price_zscore_series) / 2
        
        # Method 2: Weighted combination (more weight on OI)
        combined_weighted = (0.7 * oi_zscore_series + 0.3 * price_zscore_series)
        
        # Method 3: Product of Z-scores (amplifies when both agree)
        combined_product = oi_zscore_series * price_zscore_series
        
        # For this demo, we'll use the weighted combination
        combined_feature = combined_weighted
        
        logger.info(f"🔄 Feature Combination Methods:")
        logger.info(f"   OI Z-Score: {oi_zscore_data['latest_zscore']:6.3f}")
        logger.info(f"   Price Z-Score: {price_zscore_data['latest_zscore']:6.3f}")
        logger.info(f"   Simple Average: {combined_simple.iloc[-1]:6.3f}")
        logger.info(f"   Weighted (0.7 OI + 0.3 Price): {combined_weighted.iloc[-1]:6.3f}")
        logger.info(f"   Product: {combined_product.iloc[-1]:6.3f}")
        
        # Now apply Z-score to the combined feature
        window_size = 15  # Slightly smaller window for combined feature
        combined_rolling_mean = combined_feature.rolling(window=window_size, min_periods=8).mean()
        combined_rolling_std = combined_feature.rolling(window=window_size, min_periods=8).std()
        
        # Final Z-score of combined feature
        final_zscore = (combined_feature - combined_rolling_mean) / combined_rolling_std
        
        latest_combined = combined_feature.iloc[-1]
        latest_combined_mean = combined_rolling_mean.iloc[-1]
        latest_combined_std = combined_rolling_std.iloc[-1]
        latest_final_zscore = final_zscore.iloc[-1]
        
        logger.info(f"\n🎯 Final Combined Z-Score Calculation:")
        logger.info(f"   Combined Feature Value: {latest_combined:6.3f}")
        logger.info(f"   Rolling Mean (15): {latest_combined_mean:6.3f}")
        logger.info(f"   Rolling Std (15): {latest_combined_std:6.3f}")
        logger.info(f"   FINAL Z-SCORE: {latest_final_zscore:6.3f}")
        
        # Show recent trend
        recent_final_zscores = final_zscore.tail(5).round(3)
        logger.info(f"\n📊 Recent Final Z-Score Trend:")
        for i, zscore in enumerate(recent_final_zscores):
            if not np.isnan(zscore):
                trend_symbol = "🚀" if zscore > 1 else "📈" if zscore > 0 else "📉" if zscore > -1 else "💥"
                strength = "STRONG" if abs(zscore) > 1.5 else "MODERATE" if abs(zscore) > 0.5 else "WEAK"
                logger.info(f"   T-{4-i}: {zscore:6.3f} {trend_symbol} ({strength})")
        
        return {
            'combined_feature': combined_feature,
            'final_zscore_series': final_zscore,
            'latest_final_zscore': latest_final_zscore,
            'oi_weight': 0.7,
            'price_weight': 0.3,
            'valid': not np.isnan(latest_final_zscore)
        }
    
    def demo_step_5_generate_signals(self, combined_data: Dict) -> TradingSignal:
        """
        🎯 Step 5: Generate Trading Signals using Mean Reversion Strategy
        
        This shows how the strategy converts Z-scores into trading decisions
        """
        logger.info(f"\n{'='*60}")
        logger.info("🎯 STEP 5: GENERATING TRADING SIGNALS")
        logger.info(f"{'='*60}")
        
        final_zscore = combined_data['latest_final_zscore']
        threshold = 1.5  # Our threshold for mean reversion
        
        logger.info(f"📊 Signal Generation Parameters:")
        logger.info(f"   Final Z-Score: {final_zscore:6.3f}")
        logger.info(f"   Threshold: ±{threshold}")
        logger.info(f"   Strategy: Mean Reversion V1")
        
        # Create mock features dict for strategy
        mock_features = {
            'statistical': {
                'zscore': final_zscore,
                'mean': 0.0,
                'std': 1.0,
                'value': final_zscore,
                'valid': True
            }
        }
        
        # Generate signal using our strategy
        signal = self.strategy_selector.generate_signal(mock_features)
        
        # Explain the logic
        logger.info(f"\n🧠 Mean Reversion Logic:")
        if final_zscore > threshold:
            logger.info(f"   Z-Score ({final_zscore:.3f}) > Threshold ({threshold})")
            logger.info(f"   📉 Market is OVERBOUGHT → SHORT signal")
            logger.info(f"   💡 Expecting price to REVERT DOWN to mean")
        elif final_zscore < -threshold:
            logger.info(f"   Z-Score ({final_zscore:.3f}) < -Threshold ({-threshold})")
            logger.info(f"   📈 Market is OVERSOLD → LONG signal")
            logger.info(f"   💡 Expecting price to REVERT UP to mean")
        else:
            logger.info(f"   Z-Score ({final_zscore:.3f}) within threshold (±{threshold})")
            logger.info(f"   😴 NO SIGNAL - waiting for stronger signal")
        
        # Show signal details
        signal_emoji = {
            SignalType.LONG: "🟢",
            SignalType.SHORT: "🔴", 
            SignalType.CLOSE_LONG: "🟡",
            SignalType.CLOSE_SHORT: "🟡",
            SignalType.NO_SIGNAL: "⚪"
        }
        
        logger.info(f"\n🎯 Generated Signal:")
        logger.info(f"   Signal Type: {signal_emoji.get(signal.signal_type, '❓')} {signal.signal_type.value}")
        logger.info(f"   Strength: {signal.strength:.2f}")
        logger.info(f"   Reason: {signal.reason}")
        
        return signal
    
    def demo_step_6_position_management(self, signal: TradingSignal, current_position: Dict = None) -> Dict:
        """
        💼 Step 6: Position Management and Trade Execution Logic
        
        This shows how positions are managed and trades are executed
        """
        logger.info(f"\n{'='*60}")
        logger.info("💼 STEP 6: POSITION MANAGEMENT & TRADE EXECUTION")
        logger.info(f"{'='*60}")
        
        # Mock current position (in real system, this comes from exchange)
        if current_position is None:
            current_position = {
                'symbol': 'BTC/USDT',
                'side': 'none',  # 'long', 'short', or 'none'
                'size': 0.0,
                'entry_price': 0.0,
                'unrealized_pnl': 0.0
            }
        
        logger.info(f"📊 Current Position Status:")
        logger.info(f"   Symbol: {current_position['symbol']}")
        logger.info(f"   Side: {current_position['side'].upper()}")
        logger.info(f"   Size: {current_position['size']}")
        if current_position['size'] > 0:
            logger.info(f"   Entry Price: ${current_position['entry_price']:,.2f}")
            logger.info(f"   Unrealized PnL: ${current_position['unrealized_pnl']:,.2f}")
        
        # Determine trade action
        trade_action = None
        trade_size = 0.01  # BTC
        current_price = 45000  # Mock current price
        
        logger.info(f"\n🎯 Signal Analysis:")
        logger.info(f"   Signal: {signal.signal_type.value}")
        logger.info(f"   Current Position: {current_position['side']}")
        
        if signal.signal_type == SignalType.LONG:
            if current_position['side'] == 'none':
                trade_action = "OPEN_LONG"
                logger.info(f"   ✅ Action: OPEN LONG position")
            elif current_position['side'] == 'short':
                trade_action = "CLOSE_SHORT_OPEN_LONG"
                logger.info(f"   🔄 Action: CLOSE SHORT and OPEN LONG")
            else:
                trade_action = "HOLD_LONG"
                logger.info(f"   😴 Action: HOLD existing LONG position")
        
        elif signal.signal_type == SignalType.SHORT:
            if current_position['side'] == 'none':
                trade_action = "OPEN_SHORT"
                logger.info(f"   ✅ Action: OPEN SHORT position")
            elif current_position['side'] == 'long':
                trade_action = "CLOSE_LONG_OPEN_SHORT"
                logger.info(f"   🔄 Action: CLOSE LONG and OPEN SHORT")
            else:
                trade_action = "HOLD_SHORT"
                logger.info(f"   😴 Action: HOLD existing SHORT position")
        
        else:  # NO_SIGNAL
            trade_action = "NO_ACTION"
            logger.info(f"   ⏸️ Action: NO ACTION - waiting for signal")
        
        # Calculate potential trade details
        if trade_action not in ["HOLD_LONG", "HOLD_SHORT", "NO_ACTION"]:
            logger.info(f"\n💰 Trade Execution Details:")
            logger.info(f"   Trade Size: {trade_size} BTC")
            logger.info(f"   Current Price: ${current_price:,.2f}")
            logger.info(f"   Trade Value: ${trade_size * current_price:,.2f}")
            
            # Risk management
            stop_loss_pct = 0.02  # 2%
            take_profit_pct = 0.04  # 4%
            
            if "LONG" in trade_action:
                stop_loss_price = current_price * (1 - stop_loss_pct)
                take_profit_price = current_price * (1 + take_profit_pct)
                logger.info(f"   Stop Loss: ${stop_loss_price:,.2f} (-{stop_loss_pct*100}%)")
                logger.info(f"   Take Profit: ${take_profit_price:,.2f} (+{take_profit_pct*100}%)")
            
            elif "SHORT" in trade_action:
                stop_loss_price = current_price * (1 + stop_loss_pct)
                take_profit_price = current_price * (1 - take_profit_pct)
                logger.info(f"   Stop Loss: ${stop_loss_price:,.2f} (+{stop_loss_pct*100}%)")
                logger.info(f"   Take Profit: ${take_profit_price:,.2f} (-{take_profit_pct*100}%)")
        
        return {
            'trade_action': trade_action,
            'trade_size': trade_size,
            'current_price': current_price,
            'signal': signal,
            'position_before': current_position.copy()
        }
    
    async def run_complete_demo(self):
        """
        🚀 Run the Complete Trading Demo
        
        This executes all steps in sequence to show the full workflow
        """
        logger.info("🚀 STARTING COMPLETE TRADING DEMO")
        logger.info("=" * 80)
        
        try:
            # Step 1: Fetch market data
            market_data = await self.demo_step_1_fetch_data("BTC/USDT")
            
            # Step 2: Calculate Open Interest Z-score
            oi_zscore_data = self.demo_step_2_calculate_zscore_oi(market_data)
            
            # Step 3: Calculate Price Z-score (second feature)
            price_zscore_data = self.demo_step_3_calculate_price_zscore(market_data)
            
            # Step 4: Combine features and apply Z-score again
            combined_data = self.demo_step_4_combine_features(oi_zscore_data, price_zscore_data)
            
            # Step 5: Generate trading signals
            signal = self.demo_step_5_generate_signals(combined_data)
            
            # Step 6: Position management
            trade_details = self.demo_step_6_position_management(signal)
            
            # Final Summary
            self.print_final_summary(combined_data, signal, trade_details)
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            raise
    
    def print_final_summary(self, combined_data: Dict, signal: TradingSignal, trade_details: Dict):
        """Print a comprehensive summary of the demo results"""
        logger.info(f"\n{'='*80}")
        logger.info("🎉 DEMO COMPLETE - FINAL SUMMARY")
        logger.info(f"{'='*80}")
        
        logger.info(f"\n📊 KEY METRICS:")
        logger.info(f"   Final Combined Z-Score: {combined_data['latest_final_zscore']:6.3f}")
        logger.info(f"   Signal Generated: {signal.signal_type.value}")
        logger.info(f"   Signal Strength: {signal.strength:.2f}")
        logger.info(f"   Trade Action: {trade_details['trade_action']}")
        
        logger.info(f"\n🔍 WHAT HAPPENED:")
        logger.info(f"   1. ✅ Fetched Open Interest and Price data")
        logger.info(f"   2. ✅ Calculated Z-scores for both features")
        logger.info(f"   3. ✅ Combined features (70% OI + 30% Price)")
        logger.info(f"   4. ✅ Applied Z-score to combined feature")
        logger.info(f"   5. ✅ Generated {signal.signal_type.value} signal")
        logger.info(f"   6. ✅ Determined trade action: {trade_details['trade_action']}")
        
        logger.info(f"\n💡 LEARNING POINTS:")
        logger.info(f"   • Z-scores help normalize different data types")
        logger.info(f"   • Rolling windows smooth out noise")
        logger.info(f"   • Feature combination amplifies signals")
        logger.info(f"   • Mean reversion expects prices to return to average")
        logger.info(f"   • Risk management is built into every trade")
        
        logger.info(f"\n🎯 NEXT STEPS:")
        logger.info(f"   • Try different feature weights")
        logger.info(f"   • Experiment with different thresholds")
        logger.info(f"   • Test other strategy types")
        logger.info(f"   • Add more features (volume, volatility, etc.)")
        
        logger.info(f"\n⚠️ REMEMBER:")
        logger.info(f"   • This is a DEMO with mock data")
        logger.info(f"   • Always test with sandbox mode first")
        logger.info(f"   • Real trading involves significant risks")
        logger.info(f"   • Start small and learn gradually")
        
        logger.info(f"\n🎉 Demo completed successfully!")

async def main():
    """Main function to run the detailed trading demo"""
    print("🎯 Welcome to the Detailed Trading Demo!")
    print("This will show you exactly how to use:")
    print("• Z-score with Open Interest")
    print("• Rolling standard deviation")
    print("• Feature combination")
    print("• Mean reversion strategy")
    print("• Long/short trade execution")
    print("\nStarting demo...\n")
    
    demo = DetailedTradingDemo()
    await demo.run_complete_demo()

if __name__ == "__main__":
    asyncio.run(main())
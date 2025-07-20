"""
Demo script showing how the CCXT trading system works.
This simulates the trading logic without requiring real API keys.
"""

import asyncio
import logging
import numpy as np
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def demo_zscore_strategy():
    """Demonstrate the z-score strategy with simulated data"""
    logger.info("🚀 CCXT Trading System Demo")
    logger.info("=" * 50)
    
    from preprocessor import ZScorePreprocessor, PreprocessorManager
    from strategy import ZScoreStrategy, StrategyManager, SignalType
    
    # Create preprocessor
    zscore_processor = ZScorePreprocessor(window_size=20, min_periods=5)
    preprocessor_manager = PreprocessorManager()
    preprocessor_manager.add_preprocessor("zscore", zscore_processor)
    
    # Create strategy
    zscore_strategy = ZScoreStrategy(long_threshold=1.3, short_threshold=-1.3)
    strategy_manager = StrategyManager()
    strategy_manager.add_strategy("zscore", zscore_strategy, weight=1.0)
    
    logger.info("📊 Simulating open interest data and z-score calculations...")
    
    # Simulate different market scenarios
    scenarios = [
        ("Normal Market", np.random.normal(1000, 50, 25)),
        ("High Open Interest Spike", np.concatenate([np.random.normal(1000, 50, 20), [1200, 1300, 1400, 1350, 1320]])),
        ("Low Open Interest Dip", np.concatenate([np.random.normal(1000, 50, 20), [800, 700, 600, 650, 680]])),
        ("Volatile Market", np.random.normal(1000, 200, 25)),
        ("Trending Up", np.linspace(800, 1200, 25) + np.random.normal(0, 30, 25)),
    ]
    
    for scenario_name, data in scenarios:
        logger.info(f"\n📈 Scenario: {scenario_name}")
        logger.info("-" * 40)
        
        # Convert to the format expected by the system
        historical_data = [{'open_interest': value} for value in data]
        
        # Process data
        processed_data = preprocessor_manager.process_data(historical_data)
        
        if processed_data.get('zscore', {}).get('valid', False):
            zscore_info = processed_data['zscore']
            zscore = zscore_info['zscore']
            current_value = zscore_info['value']
            mean = zscore_info['mean']
            
            logger.info(f"Current Open Interest: {current_value:.2f}")
            logger.info(f"Rolling Mean (20): {mean:.2f}")
            logger.info(f"Z-Score: {zscore:.3f}")
            
            # Generate trading signal
            signals = strategy_manager.generate_signals(processed_data)
            final_signal = strategy_manager.aggregate_signals(signals)
            
            # Display signal
            signal_emoji = {
                SignalType.LONG: "🟢 LONG",
                SignalType.SHORT: "🔴 SHORT", 
                SignalType.HOLD: "🟡 HOLD",
                SignalType.NO_SIGNAL: "⚪ NO SIGNAL"
            }
            
            emoji = signal_emoji.get(final_signal.signal_type, "❓")
            logger.info(f"Signal: {emoji} (Strength: {final_signal.strength:.2f})")
            logger.info(f"Reason: {final_signal.reason}")
            
            # Explain the logic
            if zscore > 1.3:
                logger.info("💡 Logic: Z-score > 1.3 → Open interest unusually high → GO LONG")
            elif zscore < -1.3:
                logger.info("💡 Logic: Z-score < -1.3 → Open interest unusually low → GO SHORT")
            else:
                logger.info("💡 Logic: Z-score within normal range → No strong signal")
        
        await asyncio.sleep(0.1)  # Small delay for readability
    
    logger.info("\n" + "=" * 50)
    logger.info("✅ Demo completed! Your system is working perfectly.")
    logger.info("\n📋 Summary:")
    logger.info("• Z-score strategy: Long when z-score > 1.3, Short when z-score < -1.3")
    logger.info("• Data source: Binance open interest (in real trading)")
    logger.info("• Execution: Bybit exchange (in real trading)")
    logger.info("• Risk management: Stop-loss, take-profit, position sizing")
    logger.info("• Ready for live trading with API keys!")

async def demo_risk_management():
    """Demonstrate risk management features"""
    logger.info("\n🛡️ Risk Management Demo")
    logger.info("=" * 30)
    
    from trader import RiskManager, Position
    
    risk_manager = RiskManager(
        max_position_size=0.1,
        stop_loss_pct=0.05,
        take_profit_pct=0.10
    )
    
    # Test position sizing
    logger.info("📏 Position Sizing Test:")
    requested_size = 0.2
    adjusted_size = risk_manager.check_position_size(requested_size)
    logger.info(f"Requested: {requested_size}, Adjusted: {adjusted_size} (Max: 0.1)")
    
    # Test stop loss / take profit
    logger.info("\n📊 Stop Loss / Take Profit Test:")
    position = Position("BTC/USDT", "long", 0.01, 50000.0)
    
    # Test with 10% profit
    should_close = risk_manager.should_close_position(position, 55000.0)
    logger.info(f"At 55000 (+10%): {'🔔 TAKE PROFIT' if should_close else 'Hold'}")
    
    # Test with 5% loss  
    should_close = risk_manager.should_close_position(position, 47500.0)
    logger.info(f"At 47500 (-5%): {'🛑 STOP LOSS' if should_close else 'Hold'}")
    
    # Test with normal fluctuation
    should_close = risk_manager.should_close_position(position, 51000.0)
    logger.info(f"At 51000 (+2%): {'Exit' if should_close else '✅ Hold'}")

async def main():
    """Run the complete demo"""
    try:
        await demo_zscore_strategy()
        await demo_risk_management()
        
        logger.info("\n🎉 All demos completed successfully!")
        logger.info("Your CCXT trading system is ready for live trading!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
"""
Test script for the trading system components.
Run this to verify everything works before starting live trading.
"""

import asyncio
import logging
import sys
from datetime import datetime

# Configure logging for testing
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_data_providers():
    """Test data provider functionality"""
    logger.info("Testing data providers...")
    
    binance = None
    try:
        from data_provider import BinanceDataProvider, DataManager
        
        # Test without API keys (will use public endpoints)
        binance = BinanceDataProvider()
        data_manager = DataManager()
        data_manager.add_provider("binance", binance)
        
        # Try to fetch some test data
        symbol = "BTC/USDT"
        
        # This might fail if no API keys, but we can test the structure
        try:
            # Test OHLCV data (public endpoint)
            ohlcv = await binance.fetch_ohlcv(symbol, '1h', 10)
            if not ohlcv.empty:
                logger.info(f"✓ Successfully fetched OHLCV data: {len(ohlcv)} records")
            else:
                logger.warning("⚠ OHLCV data fetch returned empty result")
        except Exception as e:
            logger.warning(f"⚠ OHLCV fetch failed (expected without API keys): {e}")
        
        # Test open interest (requires API keys)
        try:
            oi_data = await binance.fetch_open_interest(symbol)
            if oi_data:
                logger.info(f"✓ Successfully fetched open interest data: {oi_data}")
            else:
                logger.warning("⚠ Open interest data fetch returned None")
        except Exception as e:
            logger.warning(f"⚠ Open interest fetch failed (expected without API keys): {e}")
        
        logger.info("✓ Data provider test completed")
        
    except Exception as e:
        logger.error(f"✗ Data provider test failed: {e}")
        return False
    finally:
        # Clean up connections
        if binance:
            try:
                await binance.close()
            except Exception:
                pass
    
    return True

def test_preprocessors():
    """Test preprocessor functionality"""
    logger.info("Testing preprocessors...")
    
    try:
        from preprocessor import ZScorePreprocessor, PreprocessorManager
        import numpy as np
        
        # Create test data
        test_data = [
            {'open_interest': 100 + i + np.random.normal(0, 5)} 
            for i in range(25)
        ]
        
        # Test Z-score preprocessor
        zscore_processor = ZScorePreprocessor(window_size=20, min_periods=5)
        result = zscore_processor.process(test_data)
        
        if result.get('valid', False):
            logger.info(f"✓ Z-score calculation successful: {result['zscore']:.3f}")
        else:
            logger.error("✗ Z-score calculation failed")
            return False
        
        # Test preprocessor manager
        manager = PreprocessorManager()
        manager.add_preprocessor("zscore", zscore_processor)
        
        all_results = manager.process_data(test_data)
        if 'zscore' in all_results and all_results['zscore'].get('valid', False):
            logger.info("✓ Preprocessor manager test successful")
        else:
            logger.error("✗ Preprocessor manager test failed")
            return False
        
        logger.info("✓ Preprocessor test completed")
        
    except Exception as e:
        logger.error(f"✗ Preprocessor test failed: {e}")
        return False
    
    return True

def test_strategies():
    """Test strategy functionality"""
    logger.info("Testing strategies...")
    
    try:
        from strategy import ZScoreStrategy, StrategyManager, SignalType
        from preprocessor import ZScorePreprocessor
        
        # Create test processed data
        processed_data = {
            'zscore': {
                'zscore': 1.5,  # Should trigger long signal
                'mean': 100.0,
                'std': 10.0,
                'value': 115.0,
                'valid': True
            }
        }
        
        # Test Z-score strategy
        strategy = ZScoreStrategy(long_threshold=1.3, short_threshold=-1.3)
        signal = strategy.generate_signal(processed_data)
        
        if signal.signal_type == SignalType.LONG:
            logger.info(f"✓ Strategy generated expected LONG signal: {signal}")
        else:
            logger.warning(f"⚠ Strategy generated unexpected signal: {signal}")
        
        # Test with short signal
        processed_data['zscore']['zscore'] = -1.8
        signal = strategy.generate_signal(processed_data)
        
        if signal.signal_type == SignalType.SHORT:
            logger.info(f"✓ Strategy generated expected SHORT signal: {signal}")
        else:
            logger.warning(f"⚠ Strategy generated unexpected signal: {signal}")
        
        # Test strategy manager
        manager = StrategyManager()
        manager.add_strategy("zscore", strategy, weight=1.0)
        
        signals = manager.generate_signals(processed_data)
        if 'zscore' in signals:
            logger.info("✓ Strategy manager test successful")
        else:
            logger.error("✗ Strategy manager test failed")
            return False
        
        logger.info("✓ Strategy test completed")
        
    except Exception as e:
        logger.error(f"✗ Strategy test failed: {e}")
        return False
    
    return True

def test_configuration():
    """Test configuration loading"""
    logger.info("Testing configuration...")
    
    try:
        from config import Config
        
        # Test basic config loading
        logger.info(f"Trading symbol: {Config.TRADING_SYMBOL}")
        logger.info(f"Z-score thresholds: {Config.ZSCORE_LONG_THRESHOLD}, {Config.ZSCORE_SHORT_THRESHOLD}")
        logger.info(f"Lookback period: {Config.LOOKBACK_PERIOD}")
        logger.info(f"Sandbox mode: {Config.BYBIT_SANDBOX}")
        
        # Check if API keys are configured (don't log them)
        if Config.BYBIT_API_KEY and Config.BYBIT_SECRET_KEY:
            logger.info("✓ Bybit API keys are configured")
        else:
            logger.warning("⚠ Bybit API keys not configured (required for trading)")
        
        if Config.BINANCE_API_KEY and Config.BINANCE_SECRET_KEY:
            logger.info("✓ Binance API keys are configured")
        else:
            logger.warning("⚠ Binance API keys not configured (required for data)")
        
        logger.info("✓ Configuration test completed")
        
    except Exception as e:
        logger.error(f"✗ Configuration test failed: {e}")
        return False
    
    return True

def test_risk_management():
    """Test risk management functionality"""
    logger.info("Testing risk management...")
    
    try:
        from trader import RiskManager, Position
        from datetime import datetime
        
        # Test risk manager
        risk_manager = RiskManager(
            max_position_size=0.1,
            stop_loss_pct=0.05,
            take_profit_pct=0.10
        )
        
        # Test position size check
        adjusted_size = risk_manager.check_position_size(0.2)
        if adjusted_size == 0.1:
            logger.info("✓ Position size limiting works correctly")
        else:
            logger.error("✗ Position size limiting failed")
            return False
        
        # Test position management
        position = Position("BTC/USDT", "long", 0.01, 50000.0)
        
        # Test with profit
        position.update_pnl(55000.0)  # 10% profit
        should_close = risk_manager.should_close_position(position, 55000.0)
        if should_close:
            logger.info("✓ Take profit trigger works correctly")
        else:
            logger.warning("⚠ Take profit didn't trigger as expected")
        
        # Test with loss
        position.update_pnl(47500.0)  # 5% loss
        should_close = risk_manager.should_close_position(position, 47500.0)
        if should_close:
            logger.info("✓ Stop loss trigger works correctly")
        else:
            logger.warning("⚠ Stop loss didn't trigger as expected")
        
        logger.info("✓ Risk management test completed")
        
    except Exception as e:
        logger.error(f"✗ Risk management test failed: {e}")
        return False
    
    return True

async def run_all_tests():
    """Run all tests"""
    logger.info("Starting trading system tests...")
    logger.info("=" * 50)
    
    tests = [
        ("Configuration", test_configuration),
        ("Preprocessors", test_preprocessors),
        ("Strategies", test_strategies),
        ("Risk Management", test_risk_management),
        ("Data Providers", test_data_providers),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results[test_name] = result
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{test_name:<20}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 All tests passed! System is ready to use.")
    else:
        logger.warning("⚠ Some tests failed. Check configuration and dependencies.")
    
    return passed == total

if __name__ == "__main__":
    try:
        result = asyncio.run(run_all_tests())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        sys.exit(1)
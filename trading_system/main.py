"""
Main trading system that orchestrates data collection, processing, strategy execution, and trading.
"""

import asyncio
import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, Any
import signal

from config import Config, validate_config
from data_provider import DataManager, BinanceDataProvider, BybitDataProvider
from preprocessor import PreprocessorManager, ZScorePreprocessor, PercentilePreprocessor, MovingAveragePreprocessor
from strategy import StrategyManager, ZScoreStrategy, MeanReversionStrategy, TrendFollowingStrategy
from trader import Trader, RiskManager

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class TradingSystem:
    """Main trading system class"""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.preprocessor_manager = PreprocessorManager()
        self.strategy_manager = StrategyManager()
        self.trader = None
        self.running = False
        self.last_data_fetch = datetime.min
        
        # Initialize components
        self._initialize_data_providers()
        self._initialize_preprocessors()
        self._initialize_strategies()
        self._initialize_trader()
        
    def _initialize_data_providers(self):
        """Initialize data providers"""
        logger.info("Initializing data providers...")
        
        # Binance for data
        binance_provider = BinanceDataProvider(
            api_key=Config.BINANCE_API_KEY,
            secret_key=Config.BINANCE_SECRET_KEY,
            sandbox=Config.BINANCE_SANDBOX
        )
        self.data_manager.add_provider("binance", binance_provider)
        
        # Bybit as backup data source
        bybit_provider = BybitDataProvider(
            api_key=Config.BYBIT_API_KEY,
            secret_key=Config.BYBIT_SECRET_KEY,
            sandbox=Config.BYBIT_SANDBOX
        )
        self.data_manager.add_provider("bybit", bybit_provider)
        
        logger.info("Data providers initialized")
    
    def _initialize_preprocessors(self):
        """Initialize data preprocessors"""
        logger.info("Initializing preprocessors...")
        
        # Z-score preprocessor (main one for our strategy)
        zscore_preprocessor = ZScorePreprocessor(
            window_size=Config.LOOKBACK_PERIOD,
            min_periods=5
        )
        self.preprocessor_manager.add_preprocessor("zscore", zscore_preprocessor)
        
        # Additional preprocessors for more sophisticated strategies
        percentile_preprocessor = PercentilePreprocessor(
            window_size=Config.LOOKBACK_PERIOD
        )
        self.preprocessor_manager.add_preprocessor("percentile", percentile_preprocessor)
        
        ma_preprocessor = MovingAveragePreprocessor(
            window_sizes=[5, 10, 20]
        )
        self.preprocessor_manager.add_preprocessor("ma", ma_preprocessor)
        
        logger.info("Preprocessors initialized")
    
    def _initialize_strategies(self):
        """Initialize trading strategies"""
        logger.info("Initializing strategies...")
        
        # Main Z-score strategy
        zscore_strategy = ZScoreStrategy(
            long_threshold=Config.ZSCORE_LONG_THRESHOLD,
            short_threshold=Config.ZSCORE_SHORT_THRESHOLD,
            close_threshold=0.1,
            min_signal_strength=0.5
        )
        self.strategy_manager.add_strategy("zscore", zscore_strategy, weight=1.0)
        
        # Additional strategies for diversification
        mean_reversion_strategy = MeanReversionStrategy(
            zscore_threshold=1.5,
            percentile_threshold=80,
            ma_deviation_threshold=0.05
        )
        self.strategy_manager.add_strategy("mean_reversion", mean_reversion_strategy, weight=0.5)
        
        trend_following_strategy = TrendFollowingStrategy(
            ma_period=20,
            trend_strength_threshold=0.02
        )
        self.strategy_manager.add_strategy("trend_following", trend_following_strategy, weight=0.3)
        
        logger.info("Strategies initialized")
    
    def _initialize_trader(self):
        """Initialize trader"""
        logger.info("Initializing trader...")
        
        # Risk manager
        risk_manager = RiskManager(
            max_position_size=Config.MAX_POSITION_SIZE,
            stop_loss_pct=Config.STOP_LOSS_PCT,
            take_profit_pct=Config.TAKE_PROFIT_PCT,
            max_daily_loss=0.20
        )
        
        # Trader configuration for Bybit
        exchange_config = {
            'exchange_name': 'bybit',
            'api_key': Config.BYBIT_API_KEY,
            'secret_key': Config.BYBIT_SECRET_KEY,
            'sandbox': Config.BYBIT_SANDBOX
        }
        
        self.trader = Trader(exchange_config, risk_manager)
        logger.info("Trader initialized")
    
    async def fetch_and_process_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch and process market data"""
        try:
            # Fetch open interest data from primary provider (Binance)
            data = await self.data_manager.fetch_primary_open_interest(symbol, "binance")
            
            if not data:
                logger.warning(f"No data received for {symbol}")
                return {}
            
            # Store data in history
            self.data_manager.store_data(symbol, data)
            
            # Get historical data for processing
            historical_data = self.data_manager.get_historical_data(symbol, Config.LOOKBACK_PERIOD)
            
            if len(historical_data) < 5:
                logger.info(f"Not enough historical data for {symbol}: {len(historical_data)} points")
                return {}
            
            # Process data with all preprocessors
            processed_data = self.preprocessor_manager.process_data(historical_data)
            
            logger.info(f"Processed data for {symbol}: {processed_data}")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error fetching and processing data for {symbol}: {e}")
            return {}
    
    async def generate_and_execute_signals(self, symbol: str, processed_data: Dict[str, Any]):
        """Generate trading signals and execute them"""
        try:
            # Get current position
            current_position = await self.trader.get_position(symbol)
            current_position_dict = current_position.to_dict() if current_position else None
            
            # Generate signals from all strategies
            signals = self.strategy_manager.generate_signals(processed_data, current_position_dict)
            
            if not signals:
                logger.info(f"No signals generated for {symbol}")
                return
            
            # Aggregate signals
            final_signal = self.strategy_manager.aggregate_signals(signals)
            
            logger.info(f"Final signal for {symbol}: {final_signal}")
            
            # Execute signal
            success = await self.trader.execute_signal(final_signal, symbol)
            
            if success:
                logger.info(f"Successfully executed signal for {symbol}")
            else:
                logger.warning(f"Failed to execute signal for {symbol}")
                
        except Exception as e:
            logger.error(f"Error generating and executing signals for {symbol}: {e}")
    
    async def trading_loop(self):
        """Main trading loop"""
        symbol = Config.TRADING_SYMBOL
        
        while self.running:
            try:
                loop_start_time = time.time()
                
                # Check if it's time to fetch new data
                now = datetime.now()
                if (now - self.last_data_fetch).total_seconds() >= Config.DATA_FETCH_INTERVAL:
                    
                    logger.info(f"Starting trading cycle for {symbol}")
                    
                    # Fetch and process data
                    processed_data = await self.fetch_and_process_data(symbol)
                    
                    if processed_data:
                        # Generate and execute signals
                        await self.generate_and_execute_signals(symbol, processed_data)
                    
                    # Update positions
                    await self.trader.update_positions()
                    
                    # Log portfolio summary
                    portfolio = self.trader.get_portfolio_summary()
                    logger.info(f"Portfolio summary: {portfolio}")
                    
                    self.last_data_fetch = now
                
                # Calculate sleep time to maintain interval
                loop_time = time.time() - loop_start_time
                sleep_time = max(0, 10 - loop_time)  # Check every 10 seconds minimum
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(30)  # Wait 30 seconds before retrying
    
    async def start(self):
        """Start the trading system"""
        try:
            # Validate configuration
            validate_config()
            logger.info("Configuration validated successfully")
            
            # Test connections
            await self._test_connections()
            
            self.running = True
            logger.info("Trading system started")
            
            # Start trading loop
            await self.trading_loop()
            
        except Exception as e:
            logger.error(f"Error starting trading system: {e}")
            raise
    
    async def stop(self):
        """Stop the trading system"""
        logger.info("Stopping trading system...")
        self.running = False
        
        # Close all positions (optional - you might want to keep them)
        # for symbol in list(self.trader.positions.keys()):
        #     await self.trader.close_position(symbol)
        
        logger.info("Trading system stopped")
    
    async def _test_connections(self):
        """Test connections to exchanges"""
        logger.info("Testing connections...")
        
        # Test data provider
        try:
            test_data = await self.data_manager.fetch_primary_open_interest(Config.TRADING_SYMBOL, "binance")
            if test_data:
                logger.info("Data provider connection successful")
            else:
                logger.warning("Data provider connection test returned no data")
        except Exception as e:
            logger.error(f"Data provider connection test failed: {e}")
            raise
        
        # Test trader
        try:
            balance = await self.trader.get_balance()
            logger.info(f"Trader connection successful. Balance: {balance}")
        except Exception as e:
            logger.error(f"Trader connection test failed: {e}")
            raise
        
        logger.info("All connections tested successfully")

# Global trading system instance
trading_system = None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    if trading_system:
        asyncio.create_task(trading_system.stop())

async def main():
    """Main entry point"""
    global trading_system
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Create and start trading system
        trading_system = TradingSystem()
        await trading_system.start()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        if trading_system:
            await trading_system.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.error(f"Program failed: {e}")
        sys.exit(1)
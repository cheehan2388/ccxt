# CCXT Trading System

A flexible and extensible cryptocurrency trading system built with Python and CCXT. The system fetches open interest data from Binance, processes it using z-score normalization, and executes trades on Bybit based on configurable thresholds.

## Features

- **Multi-Exchange Support**: Fetch data from Binance, trade on Bybit
- **Flexible Data Processing**: Z-score, percentile, and moving average preprocessors
- **Multiple Trading Strategies**: Z-score based, mean reversion, trend following
- **Risk Management**: Stop-loss, take-profit, position sizing, daily loss limits
- **Async Architecture**: High-performance async/await implementation
- **Comprehensive Logging**: Detailed logging for monitoring and debugging
- **Modular Design**: Easy to extend with new data sources, strategies, and exchanges

## Architecture

The system consists of several modular components:

1. **Data Providers** (`data_provider.py`): Fetch market data from exchanges
2. **Preprocessors** (`preprocessor.py`): Transform raw data (z-score, percentiles, etc.)
3. **Strategies** (`strategy.py`): Generate trading signals based on processed data
4. **Trader** (`trader.py`): Execute trades and manage positions
5. **Main System** (`main.py`): Orchestrates all components

## Installation

1. **Clone or copy the trading system files**

2. **Install dependencies**:
   ```bash
   cd trading_system
   pip install -r requirements.txt
   ```

3. **Set up configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials
   ```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Binance Configuration (for data fetching)
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
BINANCE_SANDBOX=false

# Bybit Configuration (for trading)
BYBIT_API_KEY=your_bybit_api_key_here
BYBIT_SECRET_KEY=your_bybit_secret_key_here
BYBIT_SANDBOX=true  # Set to false for live trading

# Trading Parameters
TRADING_SYMBOL=BTC/USDT
POSITION_SIZE=0.01

# Z-score Strategy Parameters
ZSCORE_LONG_THRESHOLD=1.3   # Long when z-score > 1.3
ZSCORE_SHORT_THRESHOLD=-1.3 # Short when z-score < -1.3

# Data Parameters
LOOKBACK_PERIOD=20          # Rolling window for z-score calculation
DATA_FETCH_INTERVAL=300     # Fetch data every 5 minutes

# Risk Management
MAX_POSITION_SIZE=0.1       # Maximum position size
STOP_LOSS_PCT=0.05          # 5% stop loss
TAKE_PROFIT_PCT=0.10        # 10% take profit
```

### API Keys Setup

1. **Binance API Keys** (for data):
   - Go to Binance API Management
   - Create new API key with "Read Info" permissions
   - No trading permissions needed for data fetching

2. **Bybit API Keys** (for trading):
   - Go to Bybit API Management
   - Create new API key with trading permissions
   - Start with testnet/sandbox for testing

## Usage

### Basic Usage

```bash
python main.py
```

### Advanced Usage

You can customize the system by modifying the components:

#### Adding New Data Sources

```python
# In data_provider.py
class CustomDataProvider(DataProvider):
    def __init__(self, api_key, secret_key):
        # Initialize your custom exchange
        pass
    
    async def fetch_open_interest(self, symbol):
        # Implement data fetching logic
        pass
```

#### Adding New Preprocessing Methods

```python
# In preprocessor.py
class CustomPreprocessor(Preprocessor):
    def process(self, data):
        # Implement your custom preprocessing
        return processed_result
```

#### Adding New Trading Strategies

```python
# In strategy.py
class CustomStrategy(Strategy):
    def generate_signal(self, processed_data, current_position=None):
        # Implement your trading logic
        return TradingSignal(SignalType.LONG, strength=0.8, reason="Custom signal")
```

## Trading Logic

### Z-Score Strategy

The main strategy uses z-score normalization of open interest data:

1. **Data Collection**: Fetch open interest from Binance every 5 minutes
2. **Processing**: Calculate rolling z-score with 20-period window
3. **Signal Generation**:
   - `z-score > 1.3` → LONG signal
   - `z-score < -1.3` → SHORT signal
   - `|z-score| < 0.1` → CLOSE signal (when position exists)
4. **Execution**: Place market orders on Bybit

### Risk Management

- **Position Sizing**: Limited by `MAX_POSITION_SIZE`
- **Stop Loss**: Automatic exit at 5% loss
- **Take Profit**: Automatic exit at 10% profit
- **Daily Loss Limit**: Stop trading if daily loss exceeds 20%

## Monitoring

### Logs

The system provides comprehensive logging:

```bash
tail -f trading_system.log
```

Log levels: DEBUG, INFO, WARNING, ERROR

### Portfolio Summary

The system logs portfolio summaries including:
- Current balance
- Open positions
- Unrealized PnL
- Daily PnL
- Recent orders

## Testing

### Sandbox Mode

Always test with sandbox/testnet first:

```bash
# In .env
BYBIT_SANDBOX=true
```

### Backtesting

You can extend the system to support backtesting by:
1. Creating a mock trader that simulates orders
2. Using historical data instead of live data
3. Running the same strategy logic on past data

## Safety Features

- **Sandbox by Default**: Bybit sandbox mode is enabled by default
- **Rate Limiting**: Built-in rate limiting via CCXT
- **Error Handling**: Comprehensive exception handling
- **Position Monitoring**: Continuous position and PnL monitoring
- **Graceful Shutdown**: Proper cleanup on system exit

## Extending the System

### Adding New Exchanges

1. Create a new data provider class inheriting from `DataProvider`
2. Implement required methods (`fetch_open_interest`, `fetch_ohlcv`)
3. Add to the data manager in `main.py`

### Adding New Strategies

1. Create a new strategy class inheriting from `Strategy`
2. Implement `generate_signal` method
3. Add to the strategy manager in `main.py`

### Adding New Preprocessors

1. Create a new preprocessor class inheriting from `Preprocessor`
2. Implement `process` method
3. Add to the preprocessor manager in `main.py`

## Troubleshooting

### Common Issues

1. **API Connection Errors**:
   - Verify API keys are correct
   - Check IP whitelist settings
   - Ensure proper permissions

2. **Insufficient Data**:
   - Wait for enough historical data points
   - Check data fetch interval settings

3. **Trading Errors**:
   - Verify account balance
   - Check symbol format
   - Ensure trading permissions

### Debug Mode

Enable debug logging:

```bash
# In .env
LOG_LEVEL=DEBUG
```

## Disclaimer

**This is educational software. Use at your own risk.**

- Always test thoroughly in sandbox mode first
- Never risk more than you can afford to lose
- Cryptocurrency trading involves significant risk
- Past performance does not guarantee future results

## License

This project is provided as-is for educational purposes. Use responsibly.
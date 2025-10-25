# Crypto Fetcher

A powerful CLI tool to fetch cryptocurrency data from multiple exchanges using CCXT. Get real-time prices, historical data, and more with a simple command-line interface.

## Features

- 🚀 **Multiple Exchanges**: Support for Coinbase, Kraken, OKX, KuCoin, and more
- 📊 **Real-time Data**: Live ticker prices with watch mode
- 📈 **Historical Data**: OHLCV data with customizable timeframes
- 🎨 **Beautiful Output**: Rich terminal tables, JSON, and CSV formats
- ⚡ **Fast & Reliable**: Built with CCXT for maximum compatibility
- 🔄 **Watch Mode**: Continuous monitoring with configurable intervals
- 📁 **Export Support**: Save data to files
- 🛡️ **Smart Error Handling**: User-friendly error messages with helpful suggestions

## Installation

### Using uv (Recommended)

```bash
# Clone the repository
git clone git@github.com:Algovate/crypto-fetcher.git
cd crypto-fetcher

# Install with uv
uv sync

# Install the package in development mode
uv pip install -e .
```

### Using pip

```bash
pip install crypto-fetcher
```

## Quick Start

### List Available Exchanges

```bash
crypto-fetcher exchanges
```

### Get Current Price

```bash
# Get BTC/USD price from Coinbase
crypto-fetcher ticker --exchange coinbase --symbol BTC/USD

# Watch mode with 5-second updates
crypto-fetcher ticker --exchange coinbase --symbol BTC/USD --watch --interval 5

# Save to file
crypto-fetcher ticker --exchange coinbase --symbol BTC/USD --output btc_price.json --format json
```

### Get Historical Data

```bash
# Get 100 hours of BTC/USD data
crypto-fetcher history --exchange coinbase --symbol BTC/USD --timeframe 1h --limit 100

# Get daily data for the last 30 days
crypto-fetcher history --exchange coinbase --symbol BTC/USD --timeframe 1d --limit 30 --format csv --output btc_daily.csv
```

### Multiple Symbols

```bash
# Get prices for multiple symbols
crypto-fetcher multi-ticker --exchange coinbase --symbols "BTC/USD,ETH/USD,ADA/USD"
```

## Commands

### `ticker` - Get Current Price Data

```bash
crypto-fetcher ticker [OPTIONS]

Options:
  -e, --exchange TEXT     Exchange name (required)
  -s, --symbol TEXT       Trading pair symbol (required)
  -f, --format [table|json|csv]  Output format (default: table)
  -o, --output TEXT       Save output to file
  -w, --watch            Watch mode - continuously update data
  -i, --interval INTEGER  Update interval in seconds for watch mode (default: 5)
```

**Examples:**

```bash
# Basic ticker
crypto-fetcher ticker --exchange coinbase --symbol BTC/USD

# Watch mode
crypto-fetcher ticker --exchange coinbase --symbol BTC/USD --watch

# Save as JSON
crypto-fetcher ticker --exchange coinbase --symbol BTC/USD --format json --output price.json
```

### `history` - Get Historical OHLCV Data

```bash
crypto-fetcher history [OPTIONS]

Options:
  -e, --exchange TEXT     Exchange name (required)
  -s, --symbol TEXT       Trading pair symbol (required)
  -t, --timeframe [1m|5m|15m|30m|1h|4h|1d|1w]  Timeframe (default: 1h)
  -l, --limit INTEGER     Number of records to fetch (default: 100)
  -f, --format [table|json|csv]  Output format (default: table)
  -o, --output TEXT       Save output to file
```

**Examples:**

```bash
# 1-hour candles for last 24 hours
crypto-fetcher history --exchange coinbase --symbol BTC/USD --timeframe 1h --limit 24

# Daily data for last 30 days
crypto-fetcher history --exchange coinbase --symbol BTC/USD --timeframe 1d --limit 30 --format csv
```

### `multi-ticker` - Get Multiple Symbol Prices

```bash
crypto-fetcher multi-ticker [OPTIONS]

Options:
  -e, --exchange TEXT     Exchange name (required)
  -s, --symbols TEXT      Comma-separated list of trading pairs (required)
  -f, --format [table|json|csv]  Output format (default: table)
  -o, --output TEXT       Save output to file
```

**Examples:**

```bash
# Multiple symbols
crypto-fetcher multi-ticker --exchange coinbase --symbols "BTC/USD,ETH/USD,ADA/USD"

# Save as CSV
crypto-fetcher multi-ticker --exchange coinbase --symbols "BTC/USD,ETH/USD" --format csv --output prices.csv
```

### `exchanges` - List Available Exchanges

```bash
crypto-fetcher exchanges
```

### `symbols` - List Available Trading Symbols

```bash
crypto-fetcher symbols [OPTIONS]

Options:
  -e, --exchange TEXT     Exchange name (required)
  -s, --search TEXT       Search for specific symbols (optional)
  -l, --limit INTEGER     Maximum number of symbols to display (default: 50)
```

**Examples:**

```bash
# List all symbols
crypto-fetcher symbols --exchange coinbase

# Search for BTC pairs
crypto-fetcher symbols --exchange coinbase --search BTC

# Limit results
crypto-fetcher symbols --exchange coinbase --limit 20
```

### `validate` - Validate Symbol

```bash
crypto-fetcher validate [OPTIONS]

Options:
  -e, --exchange TEXT     Exchange name (required)
  -s, --symbol TEXT       Trading pair symbol (required)
```

**Examples:**

```bash
# Check if symbol exists
crypto-fetcher validate --exchange coinbase --symbol BTC/USD
```

## Output Formats

### Table Format (Default)

Beautiful terminal tables with colors and formatting.

### JSON Format

Structured JSON output for programmatic use:

```bash
crypto-fetcher ticker --exchange coinbase --symbol BTC/USD --format json
```

### CSV Format

Comma-separated values for spreadsheet import:

```bash
crypto-fetcher history --exchange coinbase --symbol BTC/USD --format csv --output data.csv
```

## Supported Exchanges

- **Coinbase** - Popular US exchange (✅ Available)
- **Kraken** - Established exchange (✅ Available)
- **OKX** - Global exchange (✅ Available)
- **KuCoin** - Altcoin exchange (✅ Available)
- **Binance** - Largest crypto exchange (⚠️ Geographic restrictions)
- **Bybit** - Derivatives exchange (⚠️ Geographic restrictions)
- **Huobi** - Asian exchange (⚠️ Geographic restrictions)

## Timeframes

- `1m` - 1 minute
- `5m` - 5 minutes
- `15m` - 15 minutes
- `30m` - 30 minutes
- `1h` - 1 hour
- `4h` - 4 hours
- `1d` - 1 day
- `1w` - 1 week

## Examples

### Real-time Price Monitoring

```bash
# Watch BTC price with 2-second updates
crypto-fetcher ticker --exchange coinbase --symbol BTC/USD --watch --interval 2
```

### Export Historical Data

```bash
# Export 1000 hours of 1-minute data
crypto-fetcher history --exchange coinbase --symbol BTC/USD --timeframe 1m --limit 1000 --format csv --output btc_1m.csv
```

### Portfolio Monitoring

```bash
# Check multiple coins
crypto-fetcher multi-ticker --exchange coinbase --symbols "BTC/USD,ETH/USD,ADA/USD,SOL/USD"
```

## Error Handling

The tool provides user-friendly error messages with helpful suggestions:
- 🌐 **Network Errors**: Clear connection issue guidance
- ❌ **Invalid Exchanges**: Shows available exchanges
- 🔍 **Invalid Symbols**: Provides search suggestions
- ⏱️ **Rate Limiting**: Suggests waiting and retrying
- 🌍 **Geographic Restrictions**: Explains regional limitations
- 🔧 **Service Maintenance**: Indicates temporary unavailability

### Example Error Messages
```bash
❌ Exchange 'invalid_exchange' is not available.
Available exchanges: coinbase, kraken, okx, kucoin

❌ BTC/INVALID is not available on coinbase
💡 Try: crypto-fetcher symbols --exchange coinbase --search BTC
```

## Development

### Setup Development Environment

```bash
# Install dependencies
uv sync

# Install in development mode
uv pip install -e .

# Run tests
pytest
```

### Adding New Exchanges

The tool uses CCXT, so adding new exchanges is as simple as adding them to the `CryptoFetcher` class in `fetcher.py`.

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions:

- Check the [Issues](https://github.com/your-repo/crypto-fetcher/issues) page
- Create a new issue with detailed information
- Include exchange, symbol, and error messages

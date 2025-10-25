"""Core data fetching functionality using CCXT."""

import ccxt
from typing import Dict, List, Optional, Any
import time


class CryptoFetcher:
    """Main class for fetching cryptocurrency data from various exchanges."""

    def __init__(self):
        self.exchanges = {}
        self._initialize_exchanges()

    def _initialize_exchanges(self):
        """Initialize supported exchanges."""
        exchange_configs = {
            'binance': ccxt.binance(),
            'coinbase': ccxt.coinbase(),
            'kraken': ccxt.kraken(),
            'bybit': ccxt.bybit(),
            'okx': ccxt.okx(),
            'huobi': ccxt.huobi(),
            'kucoin': ccxt.kucoin(),
        }
        
        for name, exchange in exchange_configs.items():
            try:
                # Test if exchange is available
                exchange.load_markets()
                self.exchanges[name] = exchange
            except Exception as e:
                # Suppress initialization warnings - they'll be handled gracefully
                pass

    def get_available_exchanges(self) -> List[str]:
        """Get list of available exchanges."""
        return list(self.exchanges.keys())

    def get_exchange_symbols(self, exchange_name: str) -> List[str]:
        """Get available trading symbols for an exchange."""
        if exchange_name not in self.exchanges:
            raise ValueError(f"Exchange '{exchange_name}' not supported")

        exchange = self.exchanges[exchange_name]
        try:
            markets = exchange.load_markets()
            return list(markets.keys())
        except Exception as e:
            raise RuntimeError(f"Failed to load markets for {exchange_name}: {e}")

    def fetch_ticker(self, exchange_name: str, symbol: str) -> Dict[str, Any]:
        """Fetch current ticker data for a symbol."""
        if exchange_name not in self.exchanges:
            raise ValueError(f"Exchange '{exchange_name}' not supported")

        exchange = self.exchanges[exchange_name]

        try:
            ticker = exchange.fetch_ticker(symbol)
            return {
                'symbol': ticker['symbol'],
                'last': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'high': ticker['high'],
                'low': ticker['low'],
                'volume': ticker['baseVolume'],
                'quote_volume': ticker['quoteVolume'],
                'change': ticker['change'],
                'percentage': ticker['percentage'],
                'timestamp': ticker['timestamp'],
                'datetime': ticker['datetime'],
            }
        except Exception as e:
            raise RuntimeError(f"Failed to fetch ticker for {symbol} on {exchange_name}: {e}")

    def fetch_ohlcv(self, exchange_name: str, symbol: str, timeframe: str = '1h',
                   limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch historical OHLCV data for a symbol."""
        if exchange_name not in self.exchanges:
            raise ValueError(f"Exchange '{exchange_name}' not supported")

        exchange = self.exchanges[exchange_name]

        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

            # Convert to list of dictionaries for easier handling
            result = []
            for candle in ohlcv:
                result.append({
                    'timestamp': candle[0],
                    'datetime': exchange.iso8601(candle[0]),
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5],
                })

            return result
        except Exception as e:
            raise RuntimeError(f"Failed to fetch OHLCV for {symbol} on {exchange_name}: {e}")

    def fetch_multiple_tickers(self, exchange_name: str, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch ticker data for multiple symbols."""
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = self.fetch_ticker(exchange_name, symbol)
            except Exception as e:
                results[symbol] = {'error': str(e)}
        return results

    def validate_symbol(self, exchange_name: str, symbol: str) -> bool:
        """Validate if a symbol exists on the exchange."""
        try:
            symbols = self.get_exchange_symbols(exchange_name)
            return symbol in symbols
        except Exception:
            return False

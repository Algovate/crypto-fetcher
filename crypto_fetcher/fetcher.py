"""Core data fetching functionality using CCXT."""

import ccxt
from typing import Dict, List, Optional, Any, TypedDict
from dataclasses import dataclass


class TickerData(TypedDict):
    """Type definition for ticker data structure."""
    symbol: str
    last: Optional[float]
    bid: Optional[float]
    ask: Optional[float]
    high: Optional[float]
    low: Optional[float]
    volume: Optional[float]
    quote_volume: Optional[float]
    change: Optional[float]
    percentage: Optional[float]
    timestamp: Optional[int]
    datetime: Optional[str]


class OHLCVData(TypedDict):
    """Type definition for OHLCV data structure."""
    timestamp: int
    datetime: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class ExchangeConfig:
    """Configuration for exchange settings."""
    name: str
    max_limit: int
    enabled: bool = True


class ExchangeNotAvailableError(Exception):
    """Raised when an exchange is not available."""


class SymbolNotFoundError(Exception):
    """Raised when a symbol is not found on an exchange."""


class CryptoFetcher:
    """Main class for fetching cryptocurrency data from various exchanges."""

    # Exchange API limits to avoid timeouts
    EXCHANGE_LIMITS = {
        'binance': 1000,
        'coinbase': 300,
        'kraken': 720,
        'okx': 300,
        'kucoin': 1500,
        'bybit': 200,
        'huobi': 2000,
    }

    # Timeframe duration mappings in milliseconds
    TIMEFRAME_MS = {
        '1m': 60 * 1000,
        '5m': 5 * 60 * 1000,
        '15m': 15 * 60 * 1000,
        '30m': 30 * 60 * 1000,
        '1h': 60 * 60 * 1000,
        '4h': 4 * 60 * 60 * 1000,
        '1d': 24 * 60 * 60 * 1000,
        '1w': 7 * 24 * 60 * 60 * 1000,
    }

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
        self._validate_exchange(exchange_name)

        exchange = self.exchanges[exchange_name]
        try:
            markets = exchange.load_markets()
            return list(markets.keys())
        except Exception as e:
            raise RuntimeError(f"Failed to load markets for {exchange_name}: {e}") from e

    def _validate_exchange(self, exchange_name: str) -> None:
        """Validate that an exchange is available."""
        if exchange_name not in self.exchanges:
            raise ExchangeNotAvailableError(f"Exchange '{exchange_name}' not supported")

    def fetch_ticker(self, exchange_name: str, symbol: str) -> TickerData:
        """Fetch current ticker data for a symbol."""
        self._validate_exchange(exchange_name)
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
            if "not found" in str(e).lower() or "invalid symbol" in str(e).lower():
                raise SymbolNotFoundError(f"Symbol '{symbol}' not found on {exchange_name}") from e
            raise RuntimeError(f"Failed to fetch ticker for {symbol} on {exchange_name}: {e}") from e

    def fetch_ohlcv(self, exchange_name: str, symbol: str, timeframe: str = '1h',
                    limit: int = 100, until: Optional[int] = None) -> List[OHLCVData]:
        """Fetch historical OHLCV data for a symbol.

        Args:
            exchange_name: Name of the exchange
            symbol: Trading pair symbol (e.g., 'BTC/USD')
            timeframe: Candlestick timeframe (e.g., '1h', '1d')
            limit: Number of records to fetch
            until: End time in milliseconds (optional)

        Returns:
            List of OHLCV data dictionaries
        """
        self._validate_exchange(exchange_name)
        exchange = self.exchanges[exchange_name]

        try:
            # Smart limit handling: avoid exchange API limits
            max_limit = self._get_exchange_max_limit(exchange_name)
            if limit > max_limit:
                # Use pagination for large requests
                return self._fetch_ohlcv_paginated(exchange, symbol, timeframe, limit, until)

            # Simplified design: only two modes
            # 1. Only limit: get latest data
            # 2. limit + until: get data ending at specified time

            if until:
                # Mode 2: limit + until (get data ending at specified time)
                timeframe_ms = self._get_timeframe_ms(timeframe)
                since_time = until - (limit * timeframe_ms)
                params = {'limit': limit, 'since': since_time}
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe, **params)

                # Client-side filtering: only keep data before until time
                ohlcv = self._filter_by_until(ohlcv, until)
            else:
                # Mode 1: only limit (get latest data)
                params = {'limit': limit}
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe, **params)

            return self._convert_ohlcv_to_dict(ohlcv, exchange)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch OHLCV for {symbol} on {exchange_name}: {e}") from e

    def _convert_ohlcv_to_dict(self, ohlcv: List[List], exchange) -> List[OHLCVData]:
        """Convert OHLCV data from exchange format to dictionary format."""
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

    def _filter_by_until(self, ohlcv: List[List], until: int) -> List[List]:
        """Filter OHLCV data to only include candles before the until timestamp."""
        return [candle for candle in ohlcv if candle[0] <= until]

    def _get_timeframe_ms(self, timeframe: str) -> int:
        """Get timeframe duration in milliseconds."""
        return self.TIMEFRAME_MS.get(timeframe, 60 * 60 * 1000)  # Default to 1 hour

    def _get_exchange_max_limit(self, exchange_name: str) -> int:
        """Get maximum limit for an exchange to avoid API restrictions."""
        return self.EXCHANGE_LIMITS.get(exchange_name, 200)  # Default conservative limit

    def _fetch_ohlcv_paginated(self, exchange, symbol: str, timeframe: str,
                              total_limit: int, until: Optional[int] = None) -> List[OHLCVData]:
        """Fetch OHLCV data using pagination for large limits."""
        max_limit = self._get_exchange_max_limit(exchange.id)
        all_data = []
        remaining = total_limit

        with self._create_progress_bar(total_limit, symbol, timeframe) as (progress, task):
            if until:
                all_data = self._fetch_paginated_until(exchange, symbol, timeframe,
                                                      total_limit, until, max_limit,
                                                      progress, task, all_data, remaining)
            else:
                all_data = self._fetch_paginated_latest(exchange, symbol, timeframe,
                                                      total_limit, max_limit,
                                                      progress, task, all_data, remaining)

        return self._convert_ohlcv_to_dict(all_data, exchange)

    def _create_progress_bar(self, total_limit: int, symbol: str, timeframe: str):
        """Create and return a progress bar context manager."""
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
        from rich.console import Console

        console = Console()
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            console=console,
            transient=False
        )

        class ProgressContext:
            def __init__(self, progress, total_limit, symbol, timeframe):
                self.progress = progress
                self.task = progress.add_task(
                    f"Fetching {total_limit} {timeframe} candles for {symbol}",
                    total=total_limit
                )

            def __enter__(self):
                self.progress.start()
                return (self.progress, self.task)

            def __exit__(self, exc_type, exc_val, exc_tb):
                self.progress.stop()

        return ProgressContext(progress, total_limit, symbol, timeframe)

    def _fetch_paginated_until(self, exchange, symbol: str, timeframe: str,
                              total_limit: int, until: int, max_limit: int,
                              progress, task, all_data: List, remaining: int) -> List:
        """Fetch paginated data ending at until time."""
        timeframe_ms = self._get_timeframe_ms(timeframe)
        current_until = until

        while remaining > 0 and current_until > 0:
            page_limit = min(remaining, max_limit)
            progress.update(task, description=f"Fetching page {len(all_data)//max_limit + 1} for {symbol} (until {until})")

            since_time = current_until - (page_limit * timeframe_ms)

            try:
                page_data = self._fetch_single_page(exchange, symbol, timeframe, page_limit, since_time)
                if not page_data:
                    break

                filtered_data = self._filter_by_until(page_data, until)
                if not filtered_data:
                    break

                all_data.extend(filtered_data)
                remaining -= len(filtered_data)
                progress.update(task, completed=len(all_data))
                current_until = filtered_data[0][0] - timeframe_ms

            except Exception as e:
                if not self._retry_with_smaller_limit(e, page_limit, max_limit):
                    raise e
                max_limit = 50

        return all_data

    def _fetch_paginated_latest(self, exchange, symbol: str, timeframe: str,
                               total_limit: int, max_limit: int,
                               progress, task, all_data: List, remaining: int) -> List:
        """Fetch paginated latest data."""
        current_since = None

        while remaining > 0:
            page_limit = min(remaining, max_limit)
            progress.update(task, description=f"Fetching page {len(all_data)//max_limit + 1} for {symbol} (latest data)")

            try:
                page_data = self._fetch_single_page(exchange, symbol, timeframe, page_limit, current_since)
                if not page_data:
                    break

                all_data.extend(page_data)
                remaining -= len(page_data)
                progress.update(task, completed=len(all_data))
                current_since = page_data[0][0] - self._get_timeframe_ms(timeframe)

            except Exception as e:
                if not self._retry_with_smaller_limit(e, page_limit, max_limit):
                    raise e
                max_limit = 50

        return all_data

    def _fetch_single_page(self, exchange, symbol: str, timeframe: str,
                          page_limit: int, since: Optional[int] = None) -> List[List]:
        """Fetch a single page of OHLCV data."""
        params = {'limit': page_limit}
        if since:
            params['since'] = since
        return exchange.fetch_ohlcv(symbol, timeframe, **params)

    def _retry_with_smaller_limit(self, error: Exception, page_limit: int, max_limit: int) -> bool:
        """Retry with smaller limit if possible."""
        if page_limit > 50:
            return True  # Will retry with smaller limit
        return False

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

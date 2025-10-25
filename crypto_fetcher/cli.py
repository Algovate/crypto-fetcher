"""Main CLI interface for the crypto-fetcher tool."""

import click
import time
import sys
from typing import Optional, Callable, Any
from datetime import datetime
from rich.console import Console

try:
    from .fetcher import CryptoFetcher, ExchangeNotAvailableError, SymbolNotFoundError
    from .formatters import get_formatter
except ImportError:
    # Handle direct execution
    from fetcher import CryptoFetcher, ExchangeNotAvailableError, SymbolNotFoundError
    from formatters import get_formatter


console = Console()


def validate_exchange(func: Callable) -> Callable:
    """Decorator to validate exchange availability."""
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Find exchange parameter in args or kwargs
        exchange = None
        if 'exchange' in kwargs:
            exchange = kwargs['exchange']
        elif len(args) > 0:
            # For positional arguments, we need to check the function signature
            import inspect
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            if 'exchange' in params:
                exchange_idx = params.index('exchange')
                if exchange_idx < len(args):
                    exchange = args[exchange_idx]

        if exchange:
            fetcher = CryptoFetcher()
            if exchange not in fetcher.get_available_exchanges():
                console.print(f"[red]❌ Exchange '{exchange}' is not available.[/red]")
                console.print(f"[yellow]Available exchanges: {', '.join(fetcher.get_available_exchanges())}[/yellow]")
                sys.exit(1)
        return func(*args, **kwargs)
    return wrapper


def handle_output(data: Any, format_type: str, output_file: Optional[str]) -> None:
    """Handle output formatting and file saving."""
    if output_file:
        # For file output, always use JSON or CSV format to avoid Rich Table issues
        if format_type == 'table':
            # Convert table format to JSON for file output
            file_formatter = get_formatter('json')
        else:
            file_formatter = get_formatter(format_type)
        
        # Format data for file
        if hasattr(data, '__iter__') and not isinstance(data, (str, dict)):
            formatted_output = file_formatter.format_ohlcv(data)
        elif isinstance(data, dict) and 'symbol' in data:
            formatted_output = file_formatter.format_ticker(data)
        else:
            formatted_output = file_formatter.format_multiple_tickers(data)
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_output)
        console.print(f"[green]💾 Data saved to {output_file}[/green]")
    else:
        # Display on console using original format
        formatter = get_formatter(format_type)
        
        if hasattr(data, '__iter__') and not isinstance(data, (str, dict)):
            formatted_output = formatter.format_ohlcv(data)
        elif isinstance(data, dict) and 'symbol' in data:
            formatted_output = formatter.format_ticker(data)
        else:
            formatted_output = formatter.format_multiple_tickers(data)
        
        if format_type == 'table':
            console.print(formatted_output)
        else:
            console.print(formatted_output)


def parse_timestamp(timestamp_str: str) -> int:
    """Parse timestamp from string (ISO 8601 or Unix timestamp)."""
    try:
        if 'T' in timestamp_str or timestamp_str.count('-') >= 2:
            # ISO format
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return int(dt.timestamp() * 1000)
        else:
            # Assume Unix timestamp
            return int(timestamp_str)
    except ValueError as e:
        console.print(f"[red]❌ Invalid timestamp format: {timestamp_str}[/red]")
        console.print("[yellow]💡 Use ISO 8601 format (2024-01-31) or Unix timestamp[/yellow]")
        sys.exit(1)


@click.group()
@click.version_option(version="0.1.0")
@click.help_option('-h', '--help')
def main():
    """Crypto Fetcher - A CLI tool to fetch cryptocurrency data."""


@main.command()
@click.option('--exchange', '-e', required=True, help='Exchange name (e.g., binance, coinbase, kraken)')
@click.option('--symbol', '-s', required=True, help='Trading pair symbol (e.g., BTC/USDT)')
@click.option('--format', '-f', default='table', type=click.Choice(['table', 'json', 'csv']),
              help='Output format')
@click.option('--output', '-o', help='Save output to file')
@click.option('--watch', '-w', is_flag=True, help='Watch mode - continuously update data')
@click.option('--interval', '-i', default=5, help='Update frequency in seconds for watch mode (e.g., 5 = update every 5 seconds)')
@validate_exchange
def ticker(exchange: str, symbol: str, format: str, output: Optional[str],
          watch: bool, interval: int):
    """Fetch current ticker data for a trading pair."""
    fetcher = CryptoFetcher()

    try:
        if watch:
            _watch_ticker(fetcher, exchange, symbol, format, output, interval)
        else:
            data = fetcher.fetch_ticker(exchange, symbol)
            handle_output(data, format, output)

    except Exception as e:
        _display_friendly_error(console, e, exchange, symbol, "ticker")
        sys.exit(1)


def _watch_ticker(fetcher: CryptoFetcher, exchange: str, symbol: str,
                  format: str, output: Optional[str], interval: int) -> None:
    """Handle watch mode for ticker data."""
    console.print(f"[green]👀 Watching {symbol} on {exchange} (updating every {interval}s)[/green]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")

    update_count = 0
    start_time = time.time()

    while True:
        try:
            data = fetcher.fetch_ticker(exchange, symbol)

            # Clear screen and show new data
            console.clear()
            console.print(f"[bold blue]🚀 Crypto Fetcher - {symbol} on {exchange}[/bold blue]")

            # Show progress information
            update_count += 1
            elapsed_time = time.time() - start_time
            console.print(f"[dim]Update #{update_count} | Elapsed: {elapsed_time:.0f}s | Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")

            handle_output(data, format, output)
            time.sleep(interval)

        except KeyboardInterrupt:
            console.print("\n[yellow]⏹️  Stopped watching[/yellow]")
            break
        except Exception as e:
            _display_friendly_error(console, e, exchange, symbol, "watch")
            time.sleep(interval)


@main.command()
@click.option('--exchange', '-e', required=True, help='Exchange name')
@click.option('--symbol', '-s', required=True, help='Trading pair symbol')
@click.option('--timeframe', '-t', default='1h',
              type=click.Choice(['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']),
              help='Candlestick timeframe for historical data (1m=1min, 1h=1hour, 1d=1day)')
@click.option('--limit', '-l', default=100, help='Number of records to fetch')
@click.option('--until', help='End time (Unix timestamp or ISO 8601 format, e.g., 2024-01-31)')
@click.option('--format', '-f', default='table', type=click.Choice(['table', 'json', 'csv']),
              help='Output format')
@click.option('--output', '-o', help='Save output to file')
@validate_exchange
def history(exchange: str, symbol: str, timeframe: str, limit: int,
           until: Optional[str], format: str, output: Optional[str]):
    """Fetch historical OHLCV data for a trading pair.

    Two modes supported:
    1. Only --limit: Get latest N records
    2. --limit + --until: Get N records ending at specified time
    """
    fetcher = CryptoFetcher()

    try:
        # Parse until parameter
        until_timestamp = parse_timestamp(until) if until else None

        data = fetcher.fetch_ohlcv(exchange, symbol, timeframe, limit, until_timestamp)
        handle_output(data, format, output)

    except Exception as e:
        _display_friendly_error(console, e, exchange, symbol, "history")
        sys.exit(1)


@main.command()
@click.option('--exchange', '-e', required=True, help='Exchange name')
@click.option('--symbols', '-s', required=True, help='Comma-separated list of trading pairs')
@click.option('--format', '-f', default='table', type=click.Choice(['table', 'json', 'csv']),
              help='Output format')
@click.option('--output', '-o', help='Save output to file')
@validate_exchange
def multi_ticker(exchange: str, symbols: str, format: str, output: Optional[str]):
    """Fetch ticker data for multiple trading pairs."""
    fetcher = CryptoFetcher()
    symbol_list = [s.strip() for s in symbols.split(',')]

    try:
        # Show progress information for multiple symbols
        if len(symbol_list) > 3:
            console.print(f"[dim]Fetching data for {len(symbol_list)} symbols...[/dim]")

        data = fetcher.fetch_multiple_tickers(exchange, symbol_list)
        handle_output(data, format, output)

    except Exception as e:
        _display_friendly_error(console, e, exchange, f"multiple symbols: {', '.join(symbol_list)}", "multi-ticker")
        sys.exit(1)


@main.command()
def exchanges():
    """List available exchanges."""
    fetcher = CryptoFetcher()
    available_exchanges = fetcher.get_available_exchanges()

    console.print("[bold blue]Available Exchanges:[/bold blue]")
    for exchange in available_exchanges:
        console.print(f"  • {exchange}")


@main.command()
@click.option('--exchange', '-e', required=True, help='Exchange name')
@click.option('--search', '-s', help='Search for specific symbols (optional)')
@click.option('--limit', '-l', default=50, help='Maximum number of symbols to display')
@validate_exchange
def symbols(exchange: str, search: Optional[str], limit: int):
    """List available trading symbols for an exchange."""
    fetcher = CryptoFetcher()

    try:
        all_symbols = fetcher.get_exchange_symbols(exchange)

        if search:
            filtered_symbols = [s for s in all_symbols if search.upper() in s.upper()]
            console.print(f"[bold blue]🔍 Symbols containing '{search}' on {exchange}:[/bold blue]")
            symbols_to_show = filtered_symbols[:limit]
        else:
            console.print(f"[bold blue]📋 Available symbols on {exchange}:[/bold blue]")
            symbols_to_show = all_symbols[:limit]

        for symbol in symbols_to_show:
            console.print(f"  • {symbol}")

        if len(symbols_to_show) < len(all_symbols):
            console.print(f"[dim]... and {len(all_symbols) - len(symbols_to_show)} more symbols[/dim]")

    except Exception as e:
        _display_friendly_error(console, e, exchange, "symbols list", "symbols")
        sys.exit(1)


@main.command()
@click.option('--exchange', '-e', required=True, help='Exchange name')
@click.option('--symbol', '-s', required=True, help='Trading pair symbol')
@validate_exchange
def validate(exchange: str, symbol: str):
    """Validate if a symbol exists on an exchange."""
    fetcher = CryptoFetcher()

    try:
        is_valid = fetcher.validate_symbol(exchange, symbol)
        if is_valid:
            console.print(f"[green]✅ {symbol} is available on {exchange}[/green]")
        else:
            console.print(f"[red]❌ {symbol} is not available on {exchange}[/red]")
            console.print(f"[yellow]💡 Try: crypto-fetcher symbols --exchange {exchange} --search {symbol.split('/')[0]}[/yellow]")
    except Exception as e:
        _display_friendly_error(console, e, exchange, symbol, "validate")
        sys.exit(1)


def _display_friendly_error(console: Console, error: Exception, exchange: str, symbol: str, command: str = ""):
    """Display user-friendly error messages."""
    error_msg = str(error).lower()
    command_context = f" in {command}" if command else ""

    if isinstance(error, ExchangeNotAvailableError):
        console.print(f"[red]❌ Exchange '{exchange}' is not available[/red]")
        console.print("[yellow]💡 Try a different exchange[/yellow]")
    elif isinstance(error, SymbolNotFoundError):
        console.print(f"[red]❌ Symbol '{symbol}' not found on {exchange}[/red]")
        console.print(f"[yellow]💡 Try: crypto-fetcher symbols --exchange {exchange} --search {symbol.split('/')[0]}[/yellow]")
    elif "network" in error_msg or "connection" in error_msg or "timeout" in error_msg:
        console.print("[red]🌐 Network Error[/red]")
        console.print("[yellow]💡 Check your internet connection and try again[/yellow]")
    elif "rate limit" in error_msg or "too many requests" in error_msg:
        console.print("[red]⏱️  Rate Limit Exceeded[/red]")
        console.print("[yellow]💡 Please wait a moment and try again[/yellow]")
    elif "authentication" in error_msg or "api key" in error_msg:
        console.print("[red]🔐 Authentication Error[/red]")
        console.print("[yellow]💡 This exchange may require API credentials[/yellow]")
    elif "geographic" in error_msg or "restricted location" in error_msg:
        console.print("[red]🌍 Geographic Restriction[/red]")
        console.print("[yellow]💡 This exchange is not available in your region[/yellow]")
    elif "maintenance" in error_msg or "temporarily unavailable" in error_msg:
        console.print("[red]🔧 Service Maintenance[/red]")
        console.print("[yellow]💡 The exchange is temporarily unavailable. Please try later.[/yellow]")
    else:
        console.print(f"[red]❌ Error{command_context}: {error}[/red]")
        console.print("[yellow]💡 Try a different exchange or symbol[/yellow]")

    # Show available exchanges
    try:
        fetcher = CryptoFetcher()
        available = fetcher.get_available_exchanges()
        if available:
            console.print(f"[dim]Available exchanges: {', '.join(available)}[/dim]")
    except:
        pass


if __name__ == '__main__':
    main()

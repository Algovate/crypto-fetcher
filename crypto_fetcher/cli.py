"""Main CLI interface for the crypto-fetcher tool."""

import click
import time
import sys
from typing import List, Optional
from rich.console import Console
from rich import print as rprint
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.columns import Columns

try:
    from .fetcher import CryptoFetcher
    from .formatters import get_formatter
except ImportError:
    # Handle direct execution
    from fetcher import CryptoFetcher
    from formatters import get_formatter


console = Console()


@click.group()
@click.version_option(version="0.1.0")
@click.help_option('-h', '--help')
def main():
    """Crypto Fetcher - A CLI tool to fetch cryptocurrency data."""
    pass


@main.command()
@click.option('--exchange', '-e', required=True, help='Exchange name (e.g., binance, coinbase, kraken)')
@click.option('--symbol', '-s', required=True, help='Trading pair symbol (e.g., BTC/USDT)')
@click.option('--format', '-f', default='table', type=click.Choice(['table', 'json', 'csv']),
              help='Output format')
@click.option('--output', '-o', help='Save output to file')
@click.option('--watch', '-w', is_flag=True, help='Watch mode - continuously update data')
@click.option('--interval', '-i', default=5, help='Update frequency in seconds for watch mode (e.g., 5 = update every 5 seconds)')
def ticker(exchange: str, symbol: str, format: str, output: Optional[str],
          watch: bool, interval: int):
    """Fetch current ticker data for a trading pair."""
    fetcher = CryptoFetcher()
    formatter = get_formatter(format)

    try:
        # Check if exchange is available
        if exchange not in fetcher.get_available_exchanges():
            console.print(f"[red]❌ Exchange '{exchange}' is not available.[/red]")
            console.print(f"[yellow]Available exchanges: {', '.join(fetcher.get_available_exchanges())}[/yellow]")
            sys.exit(1)

        if watch:
            console.print(f"[green]👀 Watching {symbol} on {exchange} (updating every {interval}s)[/green]")
            console.print("[dim]Press Ctrl+C to stop[/dim]")

            while True:
                try:
                    data = fetcher.fetch_ticker(exchange, symbol)
                    formatted_output = formatter.format_ticker(data)

                    # Clear screen and show new data
                    console.clear()
                    console.print(f"[bold blue]🚀 Crypto Fetcher - {symbol} on {exchange}[/bold blue]")
                    console.print(f"[dim]Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")

                    if format == 'table':
                        console.print(formatted_output)
                    else:
                        console.print(formatted_output)

                    if output:
                        with open(output, 'w') as f:
                            f.write(formatted_output)

                    time.sleep(interval)
                except KeyboardInterrupt:
                    console.print("\n[yellow]⏹️  Stopped watching[/yellow]")
                    break
                except Exception as e:
                    _display_friendly_error(console, e, exchange, symbol)
                    time.sleep(interval)
        else:
            data = fetcher.fetch_ticker(exchange, symbol)
            formatted_output = formatter.format_ticker(data)

            if format == 'table':
                console.print(formatted_output)
            else:
                console.print(formatted_output)

            if output:
                with open(output, 'w') as f:
                    f.write(formatted_output)
                console.print(f"[green]💾 Data saved to {output}[/green]")

    except Exception as e:
        _display_friendly_error(console, e, exchange, symbol)
        sys.exit(1)


@main.command()
@click.option('--exchange', '-e', required=True, help='Exchange name')
@click.option('--symbol', '-s', required=True, help='Trading pair symbol')
@click.option('--timeframe', '-t', default='1h',
              type=click.Choice(['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']),
              help='Candlestick timeframe for historical data (1m=1min, 1h=1hour, 1d=1day)')
@click.option('--limit', '-l', default=100, help='Number of records to fetch')
@click.option('--format', '-f', default='table', type=click.Choice(['table', 'json', 'csv']),
              help='Output format')
@click.option('--output', '-o', help='Save output to file')
def history(exchange: str, symbol: str, timeframe: str, limit: int, format: str,
           output: Optional[str]):
    """Fetch historical OHLCV data for a trading pair."""
    fetcher = CryptoFetcher()
    formatter = get_formatter(format)

    try:
        # Check if exchange is available
        if exchange not in fetcher.get_available_exchanges():
            console.print(f"[red]❌ Exchange '{exchange}' is not available.[/red]")
            console.print(f"[yellow]Available exchanges: {', '.join(fetcher.get_available_exchanges())}[/yellow]")
            sys.exit(1)

        data = fetcher.fetch_ohlcv(exchange, symbol, timeframe, limit)
        formatted_output = formatter.format_ohlcv(data)

        if format == 'table':
            console.print(formatted_output)
        else:
            console.print(formatted_output)

        if output:
            with open(output, 'w') as f:
                f.write(formatted_output)
            console.print(f"[green]💾 Data saved to {output}[/green]")

    except Exception as e:
        _display_friendly_error(console, e, exchange, symbol)
        sys.exit(1)


@main.command()
@click.option('--exchange', '-e', required=True, help='Exchange name')
@click.option('--symbols', '-s', required=True, help='Comma-separated list of trading pairs')
@click.option('--format', '-f', default='table', type=click.Choice(['table', 'json', 'csv']),
              help='Output format')
@click.option('--output', '-o', help='Save output to file')
def multi_ticker(exchange: str, symbols: str, format: str, output: Optional[str]):
    """Fetch ticker data for multiple trading pairs."""
    fetcher = CryptoFetcher()
    formatter = get_formatter(format)

    symbol_list = [s.strip() for s in symbols.split(',')]

    try:
        # Check if exchange is available
        if exchange not in fetcher.get_available_exchanges():
            console.print(f"[red]❌ Exchange '{exchange}' is not available.[/red]")
            console.print(f"[yellow]Available exchanges: {', '.join(fetcher.get_available_exchanges())}[/yellow]")
            sys.exit(1)

        data = fetcher.fetch_multiple_tickers(exchange, symbol_list)
        formatted_output = formatter.format_multiple_tickers(data)

        if format == 'table':
            console.print(formatted_output)
        else:
            console.print(formatted_output)

        if output:
            with open(output, 'w') as f:
                f.write(formatted_output)
            console.print(f"[green]💾 Data saved to {output}[/green]")

    except Exception as e:
        _display_friendly_error(console, e, exchange, f"multiple symbols: {', '.join(symbol_list)}")
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
def symbols(exchange: str, search: Optional[str], limit: int):
    """List available trading symbols for an exchange."""
    fetcher = CryptoFetcher()

    try:
        # Check if exchange is available
        if exchange not in fetcher.get_available_exchanges():
            console.print(f"[red]❌ Exchange '{exchange}' is not available.[/red]")
            console.print(f"[yellow]Available exchanges: {', '.join(fetcher.get_available_exchanges())}[/yellow]")
            sys.exit(1)

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
        _display_friendly_error(console, e, exchange, "symbols list")
        sys.exit(1)


@main.command()
@click.option('--exchange', '-e', required=True, help='Exchange name')
@click.option('--symbol', '-s', required=True, help='Trading pair symbol')
def validate(exchange: str, symbol: str):
    """Validate if a symbol exists on an exchange."""
    fetcher = CryptoFetcher()

    try:
        # Check if exchange is available
        if exchange not in fetcher.get_available_exchanges():
            console.print(f"[red]❌ Exchange '{exchange}' is not available.[/red]")
            console.print(f"[yellow]Available exchanges: {', '.join(fetcher.get_available_exchanges())}[/yellow]")
            sys.exit(1)

        is_valid = fetcher.validate_symbol(exchange, symbol)
        if is_valid:
            console.print(f"[green]✅ {symbol} is available on {exchange}[/green]")
        else:
            console.print(f"[red]❌ {symbol} is not available on {exchange}[/red]")
            console.print(f"[yellow]💡 Try: crypto-fetcher symbols --exchange {exchange} --search {symbol.split('/')[0]}[/yellow]")
    except Exception as e:
        _display_friendly_error(console, e, exchange, symbol)
        sys.exit(1)


def _display_friendly_error(console: Console, error: Exception, exchange: str, symbol: str):
    """Display user-friendly error messages."""
    error_msg = str(error).lower()

    if "network" in error_msg or "connection" in error_msg or "timeout" in error_msg:
        console.print("[red]🌐 Network Error[/red]")
        console.print("[yellow]💡 Check your internet connection and try again[/yellow]")
    elif "not found" in error_msg or "invalid symbol" in error_msg:
        console.print(f"[red]❌ Symbol '{symbol}' not found on {exchange}[/red]")
        console.print(f"[yellow]💡 Try: crypto-fetcher symbols --exchange {exchange} --search {symbol.split('/')[0]}[/yellow]")
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
        console.print(f"[red]❌ Error: {error}[/red]")
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

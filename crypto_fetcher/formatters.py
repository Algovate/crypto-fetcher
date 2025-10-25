"""Output formatters for different data formats."""

import json
import csv
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich import print as rprint
import pandas as pd
from datetime import datetime


class Formatter:
    """Base formatter class."""

    def __init__(self):
        self.console = Console()

    def format_ticker(self, data: Dict[str, Any]) -> str:
        """Format ticker data."""
        raise NotImplementedError

    def format_ohlcv(self, data: List[Dict[str, Any]]) -> str:
        """Format OHLCV data."""
        raise NotImplementedError

    def format_multiple_tickers(self, data: Dict[str, Dict[str, Any]]) -> str:
        """Format multiple ticker data."""
        raise NotImplementedError


class TableFormatter(Formatter):
    """Rich table formatter for terminal display."""

    def format_ticker(self, data: Dict[str, Any]) -> str:
        """Format ticker data as a table."""
        if 'error' in data:
            return f"[red]Error: {data['error']}[/red]"

        table = Table(title=f"Ticker Data - {data['symbol']}")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")

        # Format the data with safe handling of None values
        table.add_row("Symbol", str(data.get('symbol', 'N/A')))
        table.add_row("Last Price", f"{data.get('last', 0):.8f}" if data.get('last') is not None else "N/A")
        table.add_row("Bid", f"{data.get('bid', 0):.8f}" if data.get('bid') is not None else "N/A")
        table.add_row("Ask", f"{data.get('ask', 0):.8f}" if data.get('ask') is not None else "N/A")
        table.add_row("High", f"{data.get('high', 0):.8f}" if data.get('high') is not None else "N/A")
        table.add_row("Low", f"{data.get('low', 0):.8f}" if data.get('low') is not None else "N/A")
        table.add_row("Volume", f"{data.get('volume', 0):.2f}" if data.get('volume') is not None else "N/A")
        table.add_row("Quote Volume", f"{data.get('quote_volume', 0):.2f}" if data.get('quote_volume') is not None else "N/A")
        table.add_row("Change", f"{data.get('change', 0):.8f}" if data.get('change') is not None else "N/A")
        table.add_row("Percentage", f"{data.get('percentage', 0):.2f}%" if data.get('percentage') is not None else "N/A")
        table.add_row("Timestamp", str(data.get('datetime', 'N/A')))

        return table

    def format_ohlcv(self, data: List[Dict[str, Any]]) -> str:
        """Format OHLCV data as a table."""
        if not data:
            return "[red]No data available[/red]"

        table = Table(title=f"OHLCV Data ({len(data)} records)")
        table.add_column("DateTime", style="cyan")
        table.add_column("Open", style="green")
        table.add_column("High", style="green")
        table.add_column("Low", style="red")
        table.add_column("Close", style="green")
        table.add_column("Volume", style="blue")

        for row in data:
            table.add_row(
                row['datetime'],
                f"{row['open']:.8f}",
                f"{row['high']:.8f}",
                f"{row['low']:.8f}",
                f"{row['close']:.8f}",
                f"{row['volume']:.2f}"
            )

        return table

    def format_multiple_tickers(self, data: Dict[str, Dict[str, Any]]) -> str:
        """Format multiple ticker data as a table."""
        table = Table(title=f"Multiple Tickers ({len(data)} symbols)")
        table.add_column("Symbol", style="cyan")
        table.add_column("Last Price", style="green")
        table.add_column("Volume", style="blue")
        table.add_column("Change %", style="yellow")
        table.add_column("High", style="green")
        table.add_column("Low", style="red")

        for symbol, ticker_data in data.items():
            if 'error' in ticker_data:
                table.add_row(symbol, "ERROR", "-", "-", "-", "-")
            else:
                last_price = f"{ticker_data.get('last', 0):.8f}" if ticker_data.get('last') is not None else "N/A"
                volume = f"{ticker_data.get('volume', 0):.2f}" if ticker_data.get('volume') is not None else "N/A"
                percentage = f"{ticker_data.get('percentage', 0):.2f}%" if ticker_data.get('percentage') is not None else "N/A"
                high = f"{ticker_data.get('high', 0):.8f}" if ticker_data.get('high') is not None else "N/A"
                low = f"{ticker_data.get('low', 0):.8f}" if ticker_data.get('low') is not None else "N/A"

                table.add_row(symbol, last_price, volume, percentage, high, low)

        return table


class JSONFormatter(Formatter):
    """JSON formatter for structured data output."""

    def format_ticker(self, data: Dict[str, Any]) -> str:
        """Format ticker data as JSON."""
        return json.dumps(data, indent=2, default=str)

    def format_ohlcv(self, data: List[Dict[str, Any]]) -> str:
        """Format OHLCV data as JSON."""
        return json.dumps(data, indent=2, default=str)

    def format_multiple_tickers(self, data: Dict[str, Dict[str, Any]]) -> str:
        """Format multiple ticker data as JSON."""
        return json.dumps(data, indent=2, default=str)


class CSVFormatter(Formatter):
    """CSV formatter for data export."""

    def format_ticker(self, data: Dict[str, Any]) -> str:
        """Format ticker data as CSV."""
        if 'error' in data:
            return f"Error,{data['error']}"

        # Create a single row DataFrame
        df = pd.DataFrame([data])
        return df.to_csv(index=False)

    def format_ohlcv(self, data: List[Dict[str, Any]]) -> str:
        """Format OHLCV data as CSV."""
        if not data:
            return "No data available"

        df = pd.DataFrame(data)
        return df.to_csv(index=False)

    def format_multiple_tickers(self, data: Dict[str, Dict[str, Any]]) -> str:
        """Format multiple ticker data as CSV."""
        # Flatten the data for CSV
        rows = []
        for symbol, ticker_data in data.items():
            if 'error' not in ticker_data:
                row = {'symbol': symbol}
                row.update(ticker_data)
                rows.append(row)
            else:
                rows.append({'symbol': symbol, 'error': ticker_data['error']})

        df = pd.DataFrame(rows)
        return df.to_csv(index=False)


def get_formatter(format_type: str) -> Formatter:
    """Get the appropriate formatter based on format type."""
    formatters = {
        'table': TableFormatter(),
        'json': JSONFormatter(),
        'csv': CSVFormatter(),
    }

    if format_type not in formatters:
        raise ValueError(f"Unsupported format: {format_type}. Supported formats: {list(formatters.keys())}")

    return formatters[format_type]

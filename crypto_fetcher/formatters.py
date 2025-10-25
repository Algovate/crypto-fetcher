"""Output formatters for different data formats."""

import json
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
import pandas as pd


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

    def _safe_format_number(self, value: Optional[float], precision: int = 8, 
                           suffix: str = "", fallback: str = "Not available") -> str:
        """Safely format a number with proper None handling."""
        if value is not None:
            return f"{value:.{precision}f}{suffix}"
        return fallback

    def _create_table(self, title: str, columns: List[tuple]) -> Table:
        """Create a Rich table with specified columns."""
        table = Table(title=title)
        for column_name, style in columns:
            table.add_column(column_name, style=style)
        return table


class TableFormatter(Formatter):
    """Rich table formatter for terminal display."""

    def format_ticker(self, data: Dict[str, Any]) -> str:
        """Format ticker data as a table."""
        if 'error' in data:
            return f"[red]Error: {data['error']}[/red]"

        table = self._create_table(
            f"Ticker Data - {data['symbol']}",
            [("Field", "cyan"), ("Value", "green")]
        )

        # Format the data with safe handling of None values
        table.add_row("Symbol", str(data.get('symbol', 'N/A')))
        table.add_row("Last Price", self._safe_format_number(data.get('last')))
        table.add_row("Bid", self._safe_format_number(data.get('bid')))
        table.add_row("Ask", self._safe_format_number(data.get('ask')))
        table.add_row("High", self._safe_format_number(data.get('high')))
        table.add_row("Low", self._safe_format_number(data.get('low')))
        table.add_row("Volume", self._safe_format_number(data.get('volume'), precision=2))
        table.add_row("Quote Volume", self._safe_format_number(data.get('quote_volume'), precision=2))
        table.add_row("Change", self._safe_format_number(data.get('change')))
        table.add_row("Percentage", self._safe_format_number(data.get('percentage'), precision=2, suffix="%"))
        table.add_row("Timestamp", str(data.get('datetime', '[dim]Not available[/dim]')))

        return table

    def format_ohlcv(self, data: List[Dict[str, Any]]) -> str:
        """Format OHLCV data as a table."""
        if not data:
            return "[red]No data available[/red]"

        table = self._create_table(
            f"OHLCV Data ({len(data)} records)",
            [
                ("DateTime", "cyan"),
                ("Open", "green"),
                ("High", "green"),
                ("Low", "red"),
                ("Close", "green"),
                ("Volume", "blue")
            ]
        )

        for row in data:
            table.add_row(
                row['datetime'],
                self._safe_format_number(row['open']),
                self._safe_format_number(row['high']),
                self._safe_format_number(row['low']),
                self._safe_format_number(row['close']),
                self._safe_format_number(row['volume'], precision=2)
            )

        return table

    def format_multiple_tickers(self, data: Dict[str, Dict[str, Any]]) -> str:
        """Format multiple ticker data as a table."""
        table = self._create_table(
            f"Multiple Tickers ({len(data)} symbols)",
            [
                ("Symbol", "cyan"),
                ("Last Price", "green"),
                ("Volume", "blue"),
                ("Change %", "yellow"),
                ("High", "green"),
                ("Low", "red")
            ]
        )

        for symbol, ticker_data in data.items():
            if 'error' in ticker_data:
                table.add_row(symbol, "ERROR", "-", "-", "-", "-")
            else:
                last_price = self._safe_format_number(ticker_data.get('last'))
                volume = self._safe_format_number(ticker_data.get('volume'), precision=2)
                percentage = self._safe_format_number(ticker_data.get('percentage'), precision=2, suffix="%")
                high = self._safe_format_number(ticker_data.get('high'))
                low = self._safe_format_number(ticker_data.get('low'))

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

        try:
            # Create a single row DataFrame
            df = pd.DataFrame([data])
            return df.to_csv(index=False)
        except Exception as e:
            return f"Error formatting ticker data: {e}"

    def format_ohlcv(self, data: List[Dict[str, Any]]) -> str:
        """Format OHLCV data as CSV."""
        if not data:
            return "No data available"

        try:
            df = pd.DataFrame(data)
            return df.to_csv(index=False)
        except Exception as e:
            return f"Error formatting OHLCV data: {e}"

    def format_multiple_tickers(self, data: Dict[str, Dict[str, Any]]) -> str:
        """Format multiple ticker data as CSV."""
        try:
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
        except Exception as e:
            return f"Error formatting multiple tickers data: {e}"


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

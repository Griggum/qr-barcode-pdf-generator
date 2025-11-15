"""CSV data loading and validation module."""
import csv
import sys
from pathlib import Path
from typing import List, Dict, Optional
import click


class DataEntry:
    """Represents a single data entry with ID, QR value, and barcode value."""
    
    def __init__(self, id: str, qr_value: Optional[str] = None, barcode_value: Optional[str] = None):
        self.id = id.strip() if id else ""
        self.qr_value = (qr_value.strip() if qr_value else self.id) or self.id
        self.barcode_value = (barcode_value.strip() if barcode_value else self.id) or self.id


class DataLoader:
    """Loads and validates CSV data."""
    
    def __init__(self, csv_path: str):
        """Initialize data loader with CSV file path."""
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            click.echo(f"Error: CSV file not found: {csv_path}", err=True)
            sys.exit(1)
    
    def load(self) -> List[DataEntry]:
        """Load entries from CSV file."""
        entries = []
        
        try:
            # Try UTF-8 first, fallback to other encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            file_handle = None
            
            for encoding in encodings:
                try:
                    file_handle = open(self.csv_path, 'r', encoding=encoding, newline='')
                    break
                except UnicodeDecodeError:
                    continue
            
            if file_handle is None:
                click.echo(f"Error: Cannot decode CSV file: {self.csv_path}", err=True)
                sys.exit(1)
            
            reader = csv.DictReader(file_handle)
            
            # Check for required 'id' column
            if 'id' not in reader.fieldnames:
                click.echo("Error: CSV file must have an 'id' column", err=True)
                sys.exit(1)
            
            row_num = 1  # Start at 1 because header is row 0
            for row in reader:
                row_num += 1
                
                # Skip empty rows
                if not any(row.values()):
                    continue
                
                # Get ID (required)
                entry_id = row.get('id', '').strip()
                if not entry_id:
                    click.echo(f"Warning: Row {row_num} has empty 'id', skipping", err=True)
                    continue
                
                # Get optional qr_value and barcode_value
                qr_value = row.get('qr_value', '').strip() if 'qr_value' in row else None
                barcode_value = row.get('barcode_value', '').strip() if 'barcode_value' in row else None
                
                entries.append(DataEntry(entry_id, qr_value, barcode_value))
            
            file_handle.close()
            
        except csv.Error as e:
            click.echo(f"Error: CSV parsing error: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Error: Failed to read CSV file: {e}", err=True)
            sys.exit(1)
        
        if not entries:
            click.echo("Error: No valid entries found in CSV file", err=True)
            sys.exit(1)
        
        return entries


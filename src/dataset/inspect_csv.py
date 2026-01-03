import csv

try:
    with open('data.csv', 'r') as f:
        content = f.read()
        print(f"First 50 chars: {content[:50]}")
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(f.read(1024))
            print(f"Detected delimiter: '{dialect.delimiter}'")
            print(f"Detected quotechar: '{dialect.quotechar}'")
        except Exception as e:
            print(f"Sniffer error: {e}")
            
        f.seek(0)
        # Try reading with pandas if available, or manual parsing
        lines = content.splitlines()
        print(f"Total lines: {len(lines)}")
except Exception as e:
    print(e)

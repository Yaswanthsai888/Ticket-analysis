#!/usr/bin/env python3
"""
Quick runner for the dashboard generator.
This creates the standalone HTML with all embedded data.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from generate_standalone_dashboard import generate_html_dashboard

OUTPUT = Path(__file__).parent / "data" / "output"

if __name__ == "__main__":
    try:
        print("✓ Generating standalone HTML dashboard...")
        html = generate_html_dashboard()
        
        output_path = OUTPUT / "dashboard.html"
        output_path.write_text(html, encoding='utf-8')
        
        file_size_mb = len(html) / (1024 * 1024)
        print(f"✓ Dashboard created successfully!")
        print(f"  File: {output_path}")
        print(f"  Size: {file_size_mb:.2f} MB")
        print(f"\n📊 Open in your browser:")
        print(f"   file:///{output_path}")
        
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

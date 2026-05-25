# Import and run the dashboard module
# Streamlit will execute the top-level code when this module is imported
import sys
from pathlib import Path

# Add src to path so imports work correctly
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Execute the dashboard code
import dashboard

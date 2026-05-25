import runpy
from pathlib import Path

# Execute the dashboard on every Streamlit rerun instead of relying on a cached import.
runpy.run_path(str(Path(__file__).parent / "src" / "dashboard.py"))

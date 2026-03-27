# BOQ PRO PH

Files included:
- `app.py` — Streamlit app for BOQ library browsing, project BOQ building, and CSV export
- `boq_library_ph.csv` — starter Philippine BOQ library
- `requirements.txt` — minimal dependencies

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes
- This is a **budgetary estimating starter**, not an official bid abstract.
- Replace rates with your latest supplier quotes, BAC/DPWH references, regional price adjustments, and recent awarded project data before procurement use.
- Good next upgrades:
  - scope generator from text input
  - area-based template builder (classroom, office, toilet, covered court)
  - discipline-specific markups
  - DPWH/agency code mapping

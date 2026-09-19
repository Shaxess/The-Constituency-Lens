import os
import streamlit as st
import pandas as pd

from sheets_client import get_client, get_sheet, get_public_safe_data
from aggregator import filter_reviewed

st.set_page_config(page_title="The Constituency Lens", layout="wide")
st.title("👁️ The Constituency Lens Africa")
st.subheader("Your Constituency At Lens - Nigeria Live")


@st.cache_resource
def connect():
    client = get_client()
    sheet = get_sheet(client)
    return sheet


try:
    sheet = connect()
    sheet_id = os.getenv("GOOGLE_SHEET_ID", "")
    st.success(f"Connected to Sheet: {sheet_id[:10]}...")

    records = get_public_safe_data(sheet)

    if not records:
        st.info("Connected, but no data in the sheet yet.")
    else:
        clean_records, skipped = filter_reviewed(records)

        df = pd.DataFrame(clean_records)
        st.write(f"Showing {len(df)} cleared rows (author/link excluded; unverified accusations held back).")
        st.dataframe(df, use_container_width=True)

        if skipped:
            with st.expander(f"⚠️ {skipped} row(s) awaiting review (not shown above, not in aggregates)"):
                flagged = [r for r in records if str(r.get("needs_review", "")).strip().upper() == "REVIEW"]
                st.dataframe(pd.DataFrame(flagged), use_container_width=True)
                st.caption("Clear a flag by emptying its needs_review cell in the sheet once verified.")

except Exception as e:
    st.warning(f"Demo mode: {e}")
    st.info("Run src/sheets_client.py first to connect")
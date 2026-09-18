import os
import streamlit as st
import pandas as pd

from sheets_client import get_client, get_sheet, get_public_safe_data

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
        df = pd.DataFrame(records)
        st.write(f"Showing {len(df)} public-safe rows (author/link excluded).")
        st.dataframe(df, use_container_width=True)

except Exception as e:
    st.warning(f"Demo mode: {e}")
    st.info("Run src/sheets_client.py first to connect")
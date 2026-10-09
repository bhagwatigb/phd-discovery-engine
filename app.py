# app.py
import asyncio
import streamlit as st
import pandas as pd
from discovery import run_discovery
from extractor import extract_phd_data
from database import init_db, upsert_position, get_all_positions

st.set_page_config(page_title="PhD Discovery Engine", layout="wide")
init_db()

st.title("🎯 Automated PhD Discovery Engine")
st.caption("Zero-cost pipeline powered by DuckDuckGo, Crawl4AI, and local Ollama")

col1, col2 = st.columns([1, 4])

with col1:
    # Updated to the new Streamlit API standard to remove warnings
    if st.button("🚀 Run Daily Sync", width="stretch"):
        st.info("Starting candidate URL discovery...")
        
        queue = run_discovery()
        st.write(f"Identified {len(queue)} candidate URLs.")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        new_entries = 0
        
        for i, item in enumerate(queue):
            status_text.text(f"Extracting: {item['university']} ({i+1}/{len(queue)})")
            
            extracted = asyncio.run(extract_phd_data(item["url"], item["university"]))
            if extracted:
                is_new = upsert_position(
                    entry=extracted,
                    university=item["university"],
                    region=item["region"],
                    source_url=item["url"]
                )
                if is_new:
                    new_entries += 1
                    
            progress_bar.progress((i + 1) / len(queue))
            
        status_text.text("Sync complete!")
        st.success(f"Added {new_entries} new openings.")

df = get_all_positions()
st.subheader(f"Tracked Positions ({len(df)} total)")

if not df.empty:
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        regions = st.multiselect("Filter by Region", options=df["region"].unique(), default=df["region"].unique())
    with filter_col2:
        modes = st.multiselect("Application Mode", options=df["application_mode"].unique(), default=df["application_mode"].unique())
    
    filtered_df = df[df["region"].isin(regions) & df["application_mode"].isin(modes)]
    
    st.dataframe(
        filtered_df[[
            "university", "region", "position_title", "domains", "deadline", 
            "application_mode", "pi_name", "degree_required", "application_link"
        ]],
        column_config={
            "application_link": st.column_config.LinkColumn("Application Portal")
        },
        hide_index=True,
        # Updated to the new Streamlit API standard
        width="stretch"
    )
else:
    st.info("No records found yet. Click 'Run Daily Sync' to start hunting.")

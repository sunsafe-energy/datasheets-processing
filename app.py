from parser_utils import get_conversion, get_tables, get_text
from prompt_utils import prepare_summary_chain, prepare_rag_pipeline, prepare_charge_controller_prompt

import os
import streamlit as st
import json
from dotenv import load_dotenv
import pandas as pd
from io import BytesIO

# For PDF processing
from pathlib import Path

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def process_datasheet(pdf_file):
    """
    Dummy processor: replace with your pipeline
    1. Ingest PDF
    2. Extract text/tables with Docling
    3. Generate embeddings + query vector DB
    4. Run LLM to extract JSON
    """

    # 1. Ingest PDF
    conv_res = get_conversion(pdf_file)

    # 2. Extract text/tables with Docling
    tables = get_tables(conv_res)
    texts = get_text(conv_res)

    # 3. Generate Embeddings + query vector DB

    # prepare summary chain
    summarize_chain = prepare_summary_chain(OPENAI_API_KEY)

    # Generate the table and text summaries
    table_summaries = summarize_chain.batch(tables, {"max_concurrency": 5})
    text_summaries = summarize_chain.batch(texts, {"max_concurrency": 5})

    # Prepare the RAG pipeline
    chain = prepare_rag_pipeline(texts, text_summaries, tables, table_summaries, OPENAI_API_KEY)
    prompt = prepare_charge_controller_prompt()

    # 4. Run LLM to extract JSON
    prompt_res = chain.invoke(prompt)
    res = json.loads(prompt_res)

    return res

def to_excel(data):
    """Convert list of dicts to Excel (in-memory)."""
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Specs")
    output.seek(0)
    return output

# -------------------------
# Streamlit UI
# -------------------------
st.title("⚡ Solar Datasheet Extractor Demo")

uploaded_file = st.file_uploader("Upload a datasheet (PDF)", type=["pdf"])

if uploaded_file:
    base_name = Path(uploaded_file.name).stem
    tmp_path = Path("tmp.pdf")

    # Only process once per file
    if "last_file" not in st.session_state or st.session_state.last_file != uploaded_file.name:
        with open(tmp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            results = process_datasheet(tmp_path)
            st.session_state.results = results
            st.session_state.last_file = uploaded_file.name
        finally:
            if tmp_path.exists():
                os.remove(tmp_path)

    # Retrieve stored results
    results = st.session_state.get("results", [])

    # Show as JSON
    st.subheader("🔎 Extracted Specifications")
    st.json(results)

    # Download JSON
    st.download_button(
        label="Download JSON",
        data=json.dumps(results, indent=2),
        file_name=f"{base_name}_specs.json",
        mime="application/json"
    )

    # Download Excel
    excel_data = to_excel(results)
    st.download_button(
        label="Download Excel",
        data=excel_data,
        file_name=f"{base_name}_specs.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Solar Components Datasheet Extractor

This project extracts structured specifications from solar charge controller datasheets (PDFs) using LLMs, document parsing, and retrieval-augmented generation (RAG). It provides a Streamlit web app for easy upload and download of extracted data in JSON and Excel formats.

Currently, only solar charge controller datasheets can be parsed. Support for parsing the rest of the components is coming soon.

## Features

- Upload a PDF datasheet and extract key specs (manufacturer, model, voltages, currents, etc.)
- Uses Docling for PDF parsing and LangChain for LLM-based extraction
- Download results as JSON or Excel

## Setup Instructions

### 1. Clone the Repository

```sh
git clone https://github.com/sunsafe-energy/datasheets-processing.git
cd datasheets-processing
```

### 2. Create a Virtual Environment (Recommended)

```sh
python -m venv .venv
.venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies

```sh
pip install -r requirements.txt
```

### 4. Set Up Environment Variables


Create a `.env` file in the project root. This file stores your API keys and other secrets. For this project, it should contain your OpenAI API key as shown below:

```env
# .env example for Datasheet Extractor
OPENAI_API_KEY=sk-...your-openai-api-key-here...
```

**Notes:**
- Replace `sk-...your-openai-api-key-here...` with your actual OpenAI API key.
- Do not share your API key publicly or commit your `.env` file to version control.
- If you add more environment variables in the future (e.g., for other LLM providers), add them to this file as new lines.

## Running the Application

### 1. Start the Streamlit App

```sh
streamlit run app.py
```

### 2. Using the App

- Open the provided local URL in your browser.
- Upload a solar charge controller PDF datasheet.
- View extracted specs, and download as JSON or Excel.

## File Overview

- `app.py` — Main Streamlit app
- `parser_utils.py` — PDF/text/table extraction utilities
- `prompt_utils.py` — LLM prompt and RAG pipeline setup
- `requirements.txt` — Python dependencies

## Notes

- Requires an OpenAI API key for LLM extraction.
- Only PDF datasheets are supported.
- Extraction logic can be customized in `parser_utils.py` and `prompt_utils.py`.

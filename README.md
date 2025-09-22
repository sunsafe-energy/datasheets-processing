# Solar Components Datasheet Extractor

This project extracts structured specifications from solar charge controller datasheets (PDFs) using LLMs, document parsing, and retrieval-augmented generation (RAG). It provides a FastAPI web server for uploading datasheets and downloading extracted data in JSON and Excel formats.

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


#### Using `venv` (Standard Python)

**Windows:**
```sh
python -m venv .venv
.venv\Scripts\activate
```

**Mac/Linux:**
```sh
python3 -m venv .venv
source .venv/bin/activate
```

#### Using `conda` (Alternative)

If you prefer using conda:

```sh
conda create -n datasheets python=3.10
conda activate datasheets
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

### 1. Start the FastAPI Server

```sh
uvicorn app:app --reload
```

### 2. Using the API

- Open the provided local URL (shown in the terminal) in your browser.
- Visit `/docs` for the interactive Swagger UI to test the API.
- Use the API to upload a solar charge controller PDF datasheet and download extracted specs as JSON or Excel.

## File Overview

- `app.py` — Main FastAPI app
- `parser_utils.py` — PDF/text/table extraction utilities
- `prompt_utils.py` — LLM prompt and RAG pipeline setup
- `requirements.txt` — Python dependencies

## Notes

- Requires an OpenAI API key for LLM extraction.
- Only PDF datasheets are supported.
- Extraction logic can be customized in `parser_utils.py` and `prompt_utils.py`.

## Performance Note

For fast datasheet parsing, a GPU is required. The underlying Docling model used for PDF parsing performs significantly better with GPU acceleration. Running on CPU is possible but will be much slower, especially for large or complex datasheets.

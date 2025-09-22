import os
import json
from dotenv import load_dotenv
import tempfile
import shutil
from enum import Enum
from fastapi import FastAPI, UploadFile, Form
from pydantic import BaseModel, Field, ValidationError
from typing import Union, List
import uvicorn

from parser_utils import get_conversion, get_tables, get_text
from prompt_utils import prepare_summary_chain, prepare_rag_pipeline, prepare_charge_controller_prompt


load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# ===================== ENUM =====================
class ComponentType(str, Enum):
    charge_controller = "charge_controller"
    battery = "battery"
    inverter = "inverter"
    solar_panel = "solar_panel"

# ===================== BASE MODEL =====================
class DatasheetBase(BaseModel):
    manufacturer: str = Field(..., example="Xantrex")
    model: str = Field(..., example="MPPT60")
    needs_review: bool = False

# ===================== UNION MODELS =====================
class ChargeControllerSpecs(DatasheetBase):
    voc: str = Field(..., example="150V")
    battery_voltage: str = Field(..., example="12V")
    charging_current: str = Field(..., example="60A")
    pv_power: str = Field(..., example="8000W")
    battery_power: str = Field(None, example="720W")

DatasheetResult = Union[
    ChargeControllerSpecs
]


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

# ===================== PROCESSOR =====================
def process_with_validation(pdf_path: str, component_type: ComponentType) -> List[DatasheetResult]:
    llm_array = process_datasheet(pdf_path)

    results: List[DatasheetResult] = []

    try:
        for item in llm_array:
            try:
                if component_type == ComponentType.charge_controller:
                    results.append(ChargeControllerSpecs.model_validate(item))
                else:
                    # The rest of the components are not yet available
                    results.append(DatasheetBase(
                        manufacturer=item.get("manufacturer", "Unknown"),
                        model=item.get("model", "Unknown"),
                        needs_review=True
                    ))
            except ValidationError:
                # Add fallback for invalid entries
                results.append(DatasheetBase(
                    manufacturer="Unknown",
                    model="Unknown",
                    needs_review=True
                ))
    except Exception:
        # If the whole JSON is broken, return one fallback entry
        results.append(DatasheetBase(
            manufacturer="Unknown",
            model="Unknown",
            needs_review=True
        ))

    return results

# ===================== FASTAPI APP =====================
app = FastAPI(
    title="Solar Datasheet Processor API",
    description="Upload a datasheet PDF and extract structured specs (multiple models supported)",
    version="1.3.0"
)

@app.post(
    "/process-datasheet/",
    response_model=List[DatasheetResult],
    summary="Process a datasheet PDF"
)
async def process_datasheet_api(
    file: UploadFile,
    component_type: ComponentType = Form(...)
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp_path = tmp.name
        shutil.copyfileobj(file.file, tmp)

    try:
        result = process_with_validation(tmp_path, component_type)
        return result
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ===================== RUN LOCALLY =====================
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


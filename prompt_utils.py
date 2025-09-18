import uuid

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain.storage import InMemoryStore
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import OpenAIEmbeddings

def prepare_summary_chain(key: str):
    prompt_text = """You are an assistant tasked with summarizing tables and text. \
    Give a concise summary of the table or text. Table or text chunk: {element} """
    prompt = ChatPromptTemplate.from_template(prompt_text)

    # Summary chain
    model = ChatOpenAI(temperature=0, model="gpt-4.1-mini-2025-04-14", api_key=key)
    summarize_chain = {"element": lambda x: x} | prompt | model | StrOutputParser()

    return summarize_chain

def prepare_charge_controller_prompt() -> str:
    prompt = """
    Instructions:

    You are given text and/or tables from a solar charge controller datasheet. The datasheet may describe multiple models.
    Extract the following specifications only under Standard Test Conditions (STC). If any other field is missing, return null.

    - manufacturer: The manufacturer name.
    - model: The model name or number. (capture exactly as written, even if it includes voltage/current info like "Tracer-4210AN")
    - charging_current: The maximum current sent to the battery or the charging current in Amps (e.g., "20A").
    - voc: The open-circuit voltage in Volts (e.g., "100V").
    - battery_voltage: The battery voltage in Volts (e.g., "12V", "24V", "48V", or "12/24/48V").
    - pv_power: The maximum PV input power in Watts (e.g., "400W", "1000W").
    - battery_power: The maximum output/load/battery power in Watts (e.g., "400W", "1000W").

    ---

    ### Rules for Manufacturer
    - **Manufacturer information** should be extracted only once for the entire datasheet.
    - Look for the manufacturer in this order of priority:
    1. **Header or title block** on the first page (often near the logo).
    2. **Logo text** (if available in extracted text).
    3. **Model name** (some models embed the brand, e.g., “Victron SmartSolar MPPT 100/50” → “Victron Energy”).
    4. **Footer / contact information section** (e.g., “Shenzhen Epsolar Technology Co., Ltd”).
    - If multiple names are present (e.g., distributor + OEM), choose the **original manufacturer/brand** if possible.
    - If you cannot determine the manufacturer, return `"Not specified"`.
    - Do not assign a different manufacturer for each model in the table — all models belong to the same manufacturer.

    ---

    ### Rules for PV Power
    - If PV Power is provided **per battery voltage**, create a **separate JSON object for each voltage–power pair**.
    - If PV Power is a **single value**, output one JSON object.
    - If PV Power is presented in a **table**, flatten it into multiple JSON objects (one per row/voltage).
    - If PV Power is missing but **Battery Voltage + Charging Current** are provided, calculate:
    - PV Power = Battery Voltage × Charging Current
    - Output one JSON object per supported battery voltage.
    - If PV Power cannot be determined, use `"Not specified"`.

    ---

    ### Rules for Battery Power
    - If **Battery Power** is explicitly given, use that value.
    - If missing, but **Battery Voltage** and **Charging Current** are available, calculate:
    - Battery Power = Battery Voltage × Charging Current
    - Output the calculated value in Watts.
    - If it cannot be determined, use `"Not specified"`.

    ---

    Output format:
    Return only the final result as a JSON array of objects with the following format without any additional text:
    [
    {
        "manufacturer": "EPEVER",
        "model": "Tracer-4210AN",
        "voc": "100V",
        "battery_voltage": "12V",
        "charging_current": "40A",
        "pv_power": "520W",
        "battery_power": "Not specified"
    },
    {
        "manufacturer": "EPEVER",
        "model": "Tracer-4210AN",
        "voc": "100V",
        "battery_voltage": "24V",
        "charging_current": "40A",
        "pv_power": "1040W",
        "battery_power": "Not specified"
    }
    ]

    """

    return prompt

def prepare_rag_pipeline(texts: list[str], text_summaries: list[str], tables: list[str], table_summaries: list[str], key: str) -> RunnablePassthrough:
    """Prepare a RAG pipeline with a retriever and LLM.
    Args:
        texts: List of text chunks from the document.
        text_summaries: List of summaries corresponding to the text chunks.
        tables: List of table markdown strings from the document.
        table_summaries: List of summaries corresponding to the tables.
        key: OpenAI API key.
    Returns:
        A LangChain Runnable representing the RAG pipeline.
    """

    # The vectorstore to use to index the child chunks
    vectorstore = Chroma(collection_name="summaries", embedding_function=OpenAIEmbeddings(api_key=key))

    # The storage layer for the parent documents
    store = InMemoryStore()
    id_key = "doc_id"

    # The retriever (empty to start)
    retriever = MultiVectorRetriever(
        vectorstore=vectorstore,
        docstore=store,
        id_key=id_key,
    )

    # Add texts
    doc_ids = [str(uuid.uuid4()) for _ in texts]
    summary_texts = [
        Document(page_content=s, metadata={id_key: doc_ids[i]})
        for i, s in enumerate(text_summaries)
    ]
    retriever.vectorstore.add_documents(summary_texts)
    retriever.docstore.mset(list(zip(doc_ids, texts)))

    # Add tables
    table_ids = [str(uuid.uuid4()) for _ in tables]
    summary_tables = [
        Document(page_content=s, metadata={id_key: table_ids[i]})
        for i, s in enumerate(table_summaries)
    ]
    retriever.vectorstore.add_documents(summary_tables)
    retriever.docstore.mset(list(zip(table_ids, tables)))

    # Prompt
    template = """You are an expert in interpreting datasheets for solar PV system components. Answer the question based only on the following context, which can include text and tables:
    {context}
    Question: {question}
    """

    prompt = ChatPromptTemplate.from_template(template)

    # LLM
    model = ChatOpenAI(temperature=0, model="gpt-4.1-mini-2025-04-14", api_key=key)

    # RAG pipeline
    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | model
        | StrOutputParser()
    )

    return chain
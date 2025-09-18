import pandas as pd
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker

def get_conversion(source: str):
  converter = DocumentConverter()
  conv_res = converter.convert(source)
  return conv_res

def get_tables(conv_res):
  # Export tables
  tables = []
  for table_ix, table in enumerate(conv_res.document.tables):
    table_df: pd.DataFrame = table.export_to_dataframe()
    table_mdwn = table_df.to_markdown()
    tables.append(table_mdwn)

  return tables

def get_text(conv_res):
  # Export text
  doc = conv_res.document
  chunker = HybridChunker()
  chunk_iter = chunker.chunk(dl_doc=doc)

  texts = []
  for i, chunk in enumerate(chunk_iter):
    enriched_text = chunker.contextualize(chunk=chunk)
    texts.append(enriched_text)

  return texts
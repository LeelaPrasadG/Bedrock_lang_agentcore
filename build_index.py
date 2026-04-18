"""
Run this ONCE to build the FAISS index and save it to disk.
After this, the main app loads from disk with no Bedrock calls at startup.
"""
import csv
import os
import random
import time
from typing import List

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_aws import BedrockEmbeddings
from langchain_community.vectorstores import FAISS

_ = load_dotenv()

FAISS_INDEX_PATH = "./faiss_index"
BASE_DELAY = 60         # seconds between successful calls
MAX_RETRIES = 12        # max retry attempts on throttling
BACKOFF_BASE = 2        # exponential backoff multiplier

# Disable botocore's built-in retries so our backoff has full control.
# Without this, botocore silently retries 4x before raising, wasting the budget.
_boto_config = Config(retries={"max_attempts": 1, "mode": "standard"})
_bedrock_client = boto3.client("bedrock-runtime", config=_boto_config)


def load_faq_csv(path: str) -> List[Document]:
    docs = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            q = row["question"].strip()
            a = row["answer"].strip()
            docs.append(Document(page_content=f"Q: {q}\nA: {a}"))
    return docs


def embed_with_backoff(store, doc, emb, index: int):
    """Embed a single doc with exponential backoff on ThrottlingException."""
    for attempt in range(MAX_RETRIES):
        try:
            if store is None:
                return FAISS.from_documents([doc], emb)
            else:
                store.add_documents([doc])
                return store
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ("ThrottlingException", "RequestLimitExceeded", "TooManyRequestsException"):
                wait = (BACKOFF_BASE ** attempt) + random.uniform(0, 1)
                print(f"    Throttled on doc {index} (attempt {attempt + 1}/{MAX_RETRIES}). Waiting {wait:.1f}s...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"Exceeded {MAX_RETRIES} retries for doc {index} due to throttling.")


if os.path.exists(FAISS_INDEX_PATH):
    print("Index already exists. Delete ./faiss_index/ to rebuild.")
else:
    print("Building FAISS index — 1 doc at a time with delays and retry backoff...")
    docs = load_faq_csv("./lauki_qna.csv")
    print(f"Loaded {len(docs)} docs from CSV. Starting embedding process...")
    emb = BedrockEmbeddings(model_id="cohere.embed-english-v3", client=_bedrock_client)
    print("Embedding docs and building FAISS index...")

    store = None
    for i, doc in enumerate(docs):
        print(f"  Embedding {i+1}/{len(docs)}: {doc.page_content[:60]}...")
        store = embed_with_backoff(store, doc, emb, i + 1)
        if i + 1 < len(docs):
            time.sleep(BASE_DELAY)  # base delay between calls

    store.save_local(FAISS_INDEX_PATH)
    print(f"\nDone! Index saved to {FAISS_INDEX_PATH}/")
    print("You can now run the main app — it will load from disk.")

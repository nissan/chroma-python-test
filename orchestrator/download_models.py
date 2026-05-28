import os
os.environ["FASTEMBED_CACHE_PATH"] = "/app/models"
from fastembed import TextEmbedding
print("Downloading BAAI/bge-small-en-v1.5 ...")
list(TextEmbedding("BAAI/bge-small-en-v1.5").embed(["warmup"]))
print("Model cached successfully.")

import tiktoken
print("Caching tiktoken cl100k_base encoding ...")
tiktoken.get_encoding("cl100k_base")
print("tiktoken encoding cached.")

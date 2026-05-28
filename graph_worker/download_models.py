"""Pre-download fastembed model at Docker build time."""
from fastembed import TextEmbedding
TextEmbedding("BAAI/bge-small-en-v1.5")
print("Model ready.")

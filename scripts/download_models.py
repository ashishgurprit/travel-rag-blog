"""Pre-download HuggingFace models at Docker build time."""
from sentence_transformers import SentenceTransformer
from FlagEmbedding import FlagReranker

print("Downloading intfloat/multilingual-e5-large...")
SentenceTransformer("intfloat/multilingual-e5-large")

print("Downloading BAAI/bge-reranker-base...")
FlagReranker("BAAI/bge-reranker-base", use_fp16=True)

print("All models downloaded.")

import chromadb
from chromadb.config import Settings

client = chromadb.Client(Settings(anonymized_telemetry=False))

collection = client.get_or_create_collection(
    name="contracts"
)
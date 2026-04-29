def load_corpus(folder_path: str) -> list[dict]:
    """
    Reads all .md files from a folder.
    Returns a list of dicts: [{doc_name, text}, ...]
    """
    documents = []
    for each .md file in folder_path:
        read the file content
        documents.append({
            "doc_name": filename,
            "text": file_content
        })
    return documents


def chunk_documents(documents: list[dict], 
                    chunk_size=400, 
                    chunk_overlap=50) -> list[dict]:
    """
    Splits each document into overlapping chunks.
    Returns a list of dicts: [{doc_name, chunk_index, text}, ...]
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = []
    for doc in documents:
        split_texts = splitter.split_text(doc["text"])
        for i, chunk_text in enumerate(split_texts):
            chunks.append({
                "doc_name": doc["doc_name"],
                "chunk_index": i,
                "text": chunk_text
            })
    return chunks


def embed_and_store(chunks: list[dict], collection_name="experimentiq"):
    """
    Embeds each chunk and upserts into ChromaDB.
    """
    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(collection_name)

    for chunk in chunks:
        embedding = model.encode(chunk["text"]).tolist()
        collection.upsert(
            ids=[f"{chunk['doc_name']}_chunk_{chunk['chunk_index']}"],
            embeddings=[embedding],
            documents=[chunk["text"]],
            metadatas=[{
                "doc_name": chunk["doc_name"],
                "chunk_index": chunk["chunk_index"]
            }]
        )
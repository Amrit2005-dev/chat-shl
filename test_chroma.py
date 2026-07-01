import chromadb
from sentence_transformers import SentenceTransformer

def test():
    # The actual sqlite file is inside chroma_db/data/chroma_db
    # Let's point persistent client to chroma_db/data/chroma_db
    db_path = "chroma_db/data/chroma_db"
    client = chromadb.PersistentClient(path=db_path)
    print("Collections:", client.list_collections())
    
    collection = client.get_collection("shl_catalog")
    print("Total items in collection:", collection.count())
    
    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_text = "Java developer mid-level"
    query_vector = model.encode([query_text], normalize_embeddings=True)[0].tolist()
    
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=5
    )
    print("\nQuery results for 'Java developer mid-level':")
    for i in range(len(results['ids'][0])):
        print(f"ID: {results['ids'][0][i]}")
        print(f"Name: {results['metadatas'][0][i]['name']}")
        print(f"URL: {results['metadatas'][0][i]['url']}")
        print(f"Test Type: {results['metadatas'][0][i]['test_type']}")
        print(f"Distance: {results['distances'][0][i]}")
        print("-" * 20)

if __name__ == '__main__':
    test()

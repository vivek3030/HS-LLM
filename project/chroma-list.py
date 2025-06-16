import chromadb

client = chromadb.HttpClient(host="127.0.0.1", port=8002)

collections = client.list_collections()

for col in collections:
    print(f"Collection: {col.name}")
    
#for collection in collections:
#    print(f"Deleting collection: {collection.name}")
#    client.delete_collection(name=collection.name)

#print("✅ All collections deleted.")


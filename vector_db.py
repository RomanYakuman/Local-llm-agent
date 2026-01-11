import chromadb
import uuid
from datetime import datetime

#simple RAG system that will provide some long-term memory for the model outside of the scope of context window, also should provide emphasis on the similar queries inside the context window

#initializing client, path is chroma by default, sqlite as db provider
#default embedding model for chroma is MiniLM-L6-v2
client = chromadb.PersistentClient()

chat_collection_name = 'chat_history'

#adding interaction to db
def save_interaction_embedding(user_msg:str, assistant_msg:str):
    collection = client.get_or_create_collection(name=chat_collection_name)
    now = datetime.now()
    #timestamp in the float format for metadata
    timestamp_float = now.timestamp()
    #timestampt for the interaction content in the format Y-M-D H:M
    datetime_string = now.strftime('%Y-%m-%d %H:%M')
    collection.add(
    documents=[f'[{datetime_string}] user: {user_msg} \nassistant:{assistant_msg}'],
    metadatas=[{'timestamp': timestamp_float, 'hsnw:space':'cosine'}],
    ids=[str(uuid.uuid4())]
)

#searching similar messages to the query using cosine similarity
def get_string_vector(query, res_count=2):
    collection = client.get_or_create_collection(name=chat_collection_name)
    full_text = ''
    results = collection.query(
        query_texts=[query],
        n_results=res_count
    )
    interactions = results['documents'][0]
    distances = results['distances'][0]
    for (doc, dist) in zip(interactions, distances):
        if(dist<=0.7):
            full_text += doc + '\n\n'
    full_text = full_text.strip()
    return full_text

def get_memory_block(query, res_count=2):
    rag_content = get_string_vector(query, res_count)
    memory_block = ''
    print(rag_content)
    if rag_content:
        memory_block = f"""
        <relevant_memory>
            The following are excerpts from past conversations. Use them for context.
            DATA:
            {rag_content}
        </relevant_memory>
        """
    return memory_block

def vector_chat_reset():
    try:
        client.get_collection(chat_collection_name)
    except ValueError:
        # Collection does not exist
        pass
    else:
        client.delete_collection(chat_collection_name)
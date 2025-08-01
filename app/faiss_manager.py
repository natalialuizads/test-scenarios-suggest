import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer

class FaissManager:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dim = 384
        self.index = faiss.IndexIDMap(faiss.IndexFlatIP(self.dim))
        self.id_to_idx = {}
        
    def add_scenario(self, id: int, title: str, embedding: np.ndarray = None):
        if embedding is None:
            embedding = self.model.encode([title])[0]
            
        embedding = embedding.reshape(1, -1).astype('float32')
        faiss.normalize_L2(embedding)
        
        idx = self.index.ntotal
        self.index.add_with_ids(embedding, np.array([id]))
        self.id_to_idx[id] = id
        
    def search(self, query: str, k=5) -> list[int]:
        query_embed = self.model.encode([query])[0]
        query_embed = query_embed.reshape(1, -1).astype('float32')
        faiss.normalize_L2(query_embed)
        
        distances, indices = self.index.search(query_embed, k)
        return indices[0].tolist(), distances[0].tolist()
    
    def update_from_db(self, data: dict):
        if data['operation'] in ['INSERT', 'UPDATE']:
            embedding = np.array(data['embedding'])
            self.add_scenario(data['id'], data['title'], embedding)
    
    def save_index(self, path="scenarios_index.faiss"):
        faiss.write_index(self.index, path)
    
    def load_index(self, path="scenarios_index.faiss"):
        self.index = faiss.read_index(path)
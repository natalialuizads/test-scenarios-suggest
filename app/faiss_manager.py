import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class FaissManager:
    def __init__(self):
        # Configuração para economizar memória
        self.model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        self.dim = 384
        
        # Configuração para quantização (reduz memória em ~75%)
        nlist = 50  # Número reduzido de clusters para economizar memória
        m = 8       # Número de subvetores
        nbits = 8   # Bits por subvetor (256 centroids por subvetor)
        
        quantizer = faiss.IndexFlatIP(self.dim)
        self.index = faiss.IndexIVFPQ(quantizer, self.dim, nlist, m, nbits)
        
        # Treinar o índice com dados aleatórios
        if not self.index.is_trained:
            logger.info("Treinando índice FAISS com dados aleatórios...")
            self.index.train(np.random.random((500, self.dim)).astype('float32'))
        
        self.id_to_idx = {}
        logger.info("Índice FAISS inicializado com quantização")

    def add_scenario(self, id: int, title: str, embedding: np.ndarray = None):
        if embedding is None:
            embedding = self.model.encode([title])[0]
        embedding = embedding.reshape(1, -1).astype('float32')
        faiss.normalize_L2(embedding)
        
        # Para índices IVF, precisamos adicionar com ID específico
        idx = self.index.ntotal
        self.index.add_with_ids(embedding, np.array([id]))
        self.id_to_idx[id] = idx

    def search(self, query: str, k=5) -> tuple:
        query_embed = self.model.encode([query])[0]
        query_embed = query_embed.reshape(1, -1).astype('float32')
        faiss.normalize_L2(query_embed)
        
        # Busca com o índice quantizado
        distances, indices = self.index.search(query_embed, k)
        return indices[0].tolist(), distances[0].tolist()

    def update_from_db(self, data: dict):
        if data['operation'] in ['INSERT', 'UPDATE']:
            try:
                embedding = np.array(data['embedding'])
                self.add_scenario(data['id'], data['title'], embedding)
            except Exception as e:
                logger.error(f"Erro ao atualizar índice FAISS: {str(e)}")

    def save_index(self, path="scenarios_index.faiss"):
        faiss.write_index(self.index, path)

    def load_index(self, path="scenarios_index.faiss"):
        self.index = faiss.read_index(path)
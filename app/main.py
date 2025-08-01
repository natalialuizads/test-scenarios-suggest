from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from faiss_manager import FaissManager
from db import Database
import numpy as np
import asyncio
import json
import os
import logging

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

faiss = FaissManager()
db = Database()

@app.on_event("startup")
async def startup():
    logger.info("Iniciando aplicação...")
    await db.connect()
    logger.info("Conexão com banco estabelecida")
    
    await db.create_extension()
    logger.info("Extensão pgvector ativada")
    
    # Carregar dados em lotes menores para economizar memória
    BATCH_SIZE = 200
    offset = 0
    total_loaded = 0
    
    logger.info("Carregando cenários para o índice FAISS...")
    while True:
        async with db.pool.acquire() as conn:
            records = await conn.fetch(
                "SELECT id, title FROM scenarios ORDER BY id LIMIT $1 OFFSET $2",
                BATCH_SIZE, offset
            )
            
            if not records:
                break
                
            for r in records:
                faiss.add_scenario(r['id'], r['title'])
                total_loaded += 1
                
                # Log periódico para acompanhar progresso
                if total_loaded % 1000 == 0:
                    logger.info(f"Carregados {total_loaded} cenários...")
            
            offset += BATCH_SIZE
    
    logger.info(f"Total de {total_loaded} cenários carregados no índice")
    
    # Iniciar listener para atualizações em tempo real
    asyncio.create_task(listen_db_updates())
    logger.info("Listener de atualizações iniciado")

async def listen_db_updates():
    async def callback(connection, pid, channel, payload):
        try:
            data = json.loads(payload)
            faiss.update_from_db(data)
        except Exception as e:
            logger.error(f"Erro ao processar atualização do banco: {str(e)}")
    
    await db.listen_for_updates(callback)

@app.post("/scenarios")
async def create_scenario(title: str, description: str = ""):
    embedding = faiss.model.encode([title])[0]
    record = await db.create_scenario(title, description, embedding)
    return {"id": record['id']}

@app.get("/suggest")
async def suggest_scenarios(query: str, k: int = 5):
    try:
        scenario_ids, similarities = faiss.search(query, k)
        scenarios = await db.get_scenarios_by_ids(scenario_ids)
        
        results = []
        for i, s in enumerate(scenarios):
            results.append({
                "id": s['id'],
                "title": s['title'],
                "similarity": float(similarities[i]) if i < len(similarities) else 0.0
            })
        
        # Ordenar por similaridade
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return {
            "query": query,
            "results": results
        }
    except Exception as e:
        logger.error(f"Erro na busca de sugestões: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno no processamento da busca")

@app.get("/scenarios/{id}")
async def get_scenario(id: int):
    scenario = await db.get_scenario(id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario

@app.post("/generate-test-data")
async def generate_test_data(num_records: int = 5000):  # Reduzido de 10000 para 5000
    from data_generator import generate_test_data
    await generate_test_data(num_records)
    return {"status": f"{num_records} test scenarios generated"}

@app.get("/health")
def health_check():
    return {"status": "OK"}

# Configuração para usar a porta do Render (padrão 10000)
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    logger.info(f"Iniciando servidor na porta {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
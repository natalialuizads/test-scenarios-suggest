from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from faiss_manager import FaissManager
from db import Database
import numpy as np
import asyncio
import json
import os

app = FastAPI()

# Configurar CORS
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
    await db.connect()
    await db.create_extension()
    
    # Carregar dados existentes
    records = await db.get_all_scenarios()
    for r in records:
        faiss.add_scenario(r['id'], r['title'])
    
    # Iniciar listener para atualiza��es em tempo real
    asyncio.create_task(listen_db_updates())

async def listen_db_updates():
    async def callback(connection, pid, channel, payload):
        data = json.loads(payload)
        faiss.update_from_db(data)
    
    await db.listen_for_updates(callback)

@app.post("/scenarios")
async def create_scenario(title: str, description: str = ""):
    embedding = faiss.model.encode([title])[0]
    record = await db.create_scenario(title, description, embedding)
    return {"id": record['id']}

@app.get("/suggest")
async def suggest_scenarios(query: str, k: int = 5):
    scenario_ids, similarities = faiss.search(query, k)
    scenarios = await db.get_scenarios_by_ids(scenario_ids)
    
    results = []
    for i, s in enumerate(scenarios):
        results.append({
            "id": s['id'],
            "title": s['title'],
            "similarity": similarities[i] if i < len(similarities) else 0.0
        })
    
    # Ordenar por similaridade
    results.sort(key=lambda x: x['similarity'], reverse=True)
    
    return {
        "query": query,
        "results": results
    }

@app.get("/scenarios/{id}")
async def get_scenario(id: int):
    scenario = await db.get_scenario(id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario

@app.post("/generate-test-data")
async def generate_test_data(num_records: int = 10000):
    from data_generator import generate_test_data
    await generate_test_data(num_records)
    return {"status": f"{num_records} test scenarios generated"}

@app.get("/health")
def health_check():
    return {"status": "OK"}
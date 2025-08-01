import asyncpg
import numpy as np
from pgvector.asyncpg import register_vector
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.dsn = os.getenv("DATABASE_URL")
        self.pool = None
        
    async def connect(self):
        self.pool = await asyncpg.create_pool(
            dsn=self.dsn,
            init=register_vector
        )
        
    async def get_scenario(self, id: int):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT id, title, description FROM scenarios WHERE id = $1", 
                id
            )
    
    async def get_scenarios_by_ids(self, ids: list[int]):
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                "SELECT id, title, description FROM scenarios WHERE id = ANY($1)",
                ids
            )
    
    async def create_scenario(self, title: str, description: str, embedding: np.ndarray):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "INSERT INTO scenarios (title, description, embedding) VALUES ($1, $2, $3) RETURNING id",
                title, description, embedding
            )
    
    async def listen_for_updates(self, callback):
        async with self.pool.acquire() as conn:
            await conn.add_listener('faiss_update', callback)
    
    async def get_all_scenarios(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT id, title FROM scenarios")
    
    async def create_extension(self):
        async with self.pool.acquire() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
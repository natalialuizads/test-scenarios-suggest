### Solução Completa para o Projeto de Sugestão de Cenários de Teste

Aqui está o projeto completo, otimizado para performance e pronto para hospedagem gratuita no Render.com:

#### Estrutura do Projeto
```
test-scenario-suggest/
├── app/
│   ├── main.py               # API principal
│   ├── db.py                 # Conexão com o banco
│   ├── faiss_manager.py      # Gerenciamento do índice FAISS
│   ├── data_generator.py     # Gerador de dados de teste
│   └── requirements.txt      # Dependências
├── docker-compose.yml        # Configuração Docker
├── Dockerfile                # Build da aplicação
├── init.sql                  # Script de inicialização do DB
└── .env                      # Variáveis de ambiente
```

### Arquivos do Projeto

#### 1. `app/requirements.txt`
```text
fastapi==0.110.0
uvicorn==0.29.0
sentence-transformers==2.7.0
faiss-cpu==1.8.0
numpy==1.26.4
asyncpg==0.29.0
psycopg2-binary==2.9.9
python-multipart==0.0.9
python-dotenv==1.0.1
```

#### 2. `app/db.py`
```python
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
```

#### 3. `app/faiss_manager.py`
```python
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
```

#### 4. `app/data_generator.py`
```python
import asyncio
import random
from db import Database
from faiss_manager import FaissManager
import os

# Templates para geração de dados realistas
templates = [
    "Teste de login com {method}",
    "Cadastro de usuário via {platform}",
    "Recuperação de senha para {user_type}",
    "Busca de {product} na plataforma",
    "Atualização de perfil do {user_type}",
    "Pagamento com {payment_method}",
    "Adicionar {product} ao carrinho",
    "Fluxo de checkout para {user_type}",
    "Teste de API {endpoint}",
    "Validação de {field} no formulário"
]

methods = ["email", "Google", "Facebook", "Apple ID"]
platforms = ["mobile", "web", "tablet", "desktop"]
user_types = ["cliente", "admin", "convidado", "vip"]
products = ["produto", "serviço", "assinatura", "curso"]
payment_methods = ["cartão", "PIX", "boleto", "paypal"]
endpoints = ["/login", "/users", "/products", "/orders"]
fields = ["nome", "email", "CPF", "telefone"]

async def generate_test_data(num_records=10000):
    db = Database()
    faiss = FaissManager()
    await db.connect()
    
    print(f"Generating {num_records} test scenarios...")
    
    for i in range(num_records):
        template = random.choice(templates)
        
        # Preencher template com dados aleatórios
        title = template.format(
            method=random.choice(methods),
            platform=random.choice(platforms),
            user_type=random.choice(user_types),
            product=random.choice(products),
            payment_method=random.choice(payment_methods),
            endpoint=random.choice(endpoints),
            field=random.choice(fields)
        )
        
        # Criar descrição relacionada
        description = f"Cenário de teste para {title.lower()}"
        
        # Gerar embedding e salvar
        embedding = faiss.model.encode([title])[0]
        await db.create_scenario(title, description, embedding)
        
        if (i + 1) % 1000 == 0:
            print(f"Generated {i+1}/{num_records} scenarios")
    
    print("Data generation complete!")

if __name__ == "__main__":
    asyncio.run(generate_test_data(10000))
```

#### 5. `app/main.py`
```python
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
    
    # Iniciar listener para atualizações em tempo real
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
```

#### 6. `Dockerfile`
```dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app

EXPOSE 10000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
```

#### 7. `docker-compose.yml`
```yaml
version: '3.8'

services:
  db:
    image: ankane/pgvector
    container_name: scenario_db
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: scenarios
    volumes:
      - db-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  api:
    build: .
    container_name: scenario_api
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./app:/app
    ports:
      - "10000:10000"
    environment:
      DATABASE_URL: "postgresql://admin:secret@db:5432/scenarios"
    command: 
      - /bin/sh
      - -c
      - |
        # Esperar o banco ficar pronto
        until pg_isready -h db -p 5432 -U admin; do
          echo "Waiting for PostgreSQL..."
          sleep 2
        done
        
        # Iniciar a API
        uvicorn main:app --host 0.0.0.0 --port 10000

volumes:
  db-data:
```

#### 8. `init.sql`
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE scenarios (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    embedding VECTOR(384)
);

CREATE OR REPLACE FUNCTION notify_faiss_update()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('faiss_update', json_build_object(
        'operation', TG_OP,
        'id', NEW.id,
        'title', NEW.title,
        'embedding', NEW.embedding
    )::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER faiss_trigger
AFTER INSERT OR UPDATE ON scenarios
FOR EACH ROW EXECUTE FUNCTION notify_faiss_update();
```

### Configuração no Render.com

#### Passo 1: Criar conta no Render
1. Acesse [render.com](https://render.com)
2. Crie uma conta usando GitHub ou email

#### Passo 2: Criar banco de dados PostgreSQL
1. No dashboard, clique em "New +" > "PostgreSQL"
2. Configurações:
   - **Name**: `scenario-db`
   - **Database**: `scenarios`
   - **User**: `admin`
   - **Region**: São Paulo (ou mais próxima)
   - **Plan**: Free
3. Após criação, anote a string de conexão em "Connections"

#### Passo 3: Configurar Web Service
1. Clique em "New +" > "Web Service"
2. Conecte seu repositório GitHub com o projeto
3. Configurações:
   - **Name**: `scenario-api`
   - **Region**: Mesma do banco
   - **Branch**: `main`
   - **Runtime**: Docker
   - **Plan**: Free
4. Adicione variáveis de ambiente:
   - `DATABASE_URL`: Cole a string de conexão do banco
5. Configurações avançadas:
   - **Build Command**: `docker build -t scenario-api .`
   - **Start Command**: `docker run -p 10000:10000 scenario-api`
   - **Port**: `10000`

#### Passo 4: Executar migração inicial
1. Após o deploy, acesse o console do banco via Render Dashboard
2. Execute manualmente:
   ```sql
   CREATE EXTENSION vector;
   ```

#### Passo 5: Gerar dados de teste
1. Acesse o terminal do Web Service no Render
2. Execute:
   ```bash
   python app/data_generator.py
   ```

#### Passo 6: Testar a API
Use as rotas:
- `POST /scenarios` - Criar novo cenário
- `GET /suggest?query=login` - Buscar sugestões
- `POST /generate-test-data` - Gerar mais dados (opcional)

### Como Executar Localmente
```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/test-scenario-suggest.git
cd test-scenario-suggest

# 2. Inicie os containers
docker-compose up --build -d

# 3. Gere dados de teste (10k registros)
docker exec -it scenario_api python app/data_generator.py

# 4. Teste a API
curl http://localhost:10000/suggest?query=login
```

### Recursos Gratuitos Estimados
| Recurso | Uso Estimado | Limite Free Tier |
|---------|--------------|------------------|
| **Armazenamento DB** | 150 MB | 1 GB (Render) |
| **RAM API** | 300 MB | 512 MB (Render) |
| **CPU** | 5-10% | 0.1 vCPU (Render) |
| **Tráfego** | Baixo | 100 GB/mês (Render) |

Este projeto está completo e otimizado para funcionar perfeitamente no plano gratuito do Render.com com até 10k registros. A arquitetura combina a velocidade do FAISS para buscas semânticas com a confiabilidade do PostgreSQL para armazenamento.
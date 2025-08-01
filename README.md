# Test Scenario Suggester API

API para sugestão de cenários de teste usando FAISS e PostgreSQL

## Pré-requisitos
- Docker
- Docker Compose

## Configuração Inicial
1. Crie o arquivo `.env`:
```bash
cp .env.example .env
# Edite com suas credenciais
```

2. Construa e inicie os containers:
```bash
docker-compose up --build -d
```

3. Gere dados de teste (opcional):
```bash
docker exec -it scenario_api python app/data_generator.py
```

## Endpoints
- `POST /scenarios` - Criar novo cenário
- `GET /suggest?query=texto` - Buscar sugestões
- `POST /generate-test-data` - Gerar dados de teste
- `GET /health` - Verificar saúde da API

## Variáveis de Ambiente
| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DB_USER` | Usuário do PostgreSQL | admin |
| `DB_PASSWORD` | Senha do PostgreSQL | - |
| `DB_NAME` | Nome do banco | scenarios |
```


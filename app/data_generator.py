import asyncio
import random
from db import Database
from faiss_manager import FaissManager
import os
import logging

logger = logging.getLogger(__name__)

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

async def generate_test_data(num_records=5000):  # Reduzido de 10000 para 5000
    logger.info(f"Gerando {num_records} cenários de teste...")
    
    db = Database()
    faiss = FaissManager()
    
    await db.connect()
    
    BATCH_SIZE = 200
    total_generated = 0
    
    for i in range(0, num_records, BATCH_SIZE):
        batch_end = min(i + BATCH_SIZE, num_records)
        logger.info(f"Gerando cenários {i+1} a {batch_end}...")
        
        async with db.pool.acquire() as conn:
            for j in range(i, batch_end):
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
                await conn.execute(
                    "INSERT INTO scenarios (title, description, embedding) VALUES ($1, $2, $3)",
                    title, description, embedding
                )
                total_generated += 1
                
                if total_generated % 500 == 0:
                    logger.info(f"Gerados {total_generated}/{num_records} cenários")
    
    logger.info(f"Geração de dados concluída! Total: {total_generated} cenários")
    return total_generated

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(generate_test_data(5000))
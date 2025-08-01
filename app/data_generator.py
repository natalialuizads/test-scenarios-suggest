import asyncio
import random
from db import Database
from faiss_manager import FaissManager
import os
import logging

logger = logging.getLogger(__name__)

# Templates para gera��o de dados realistas
templates = [
    "Teste de login com {method}",
    "Cadastro de usu�rio via {platform}",
    "Recupera��o de senha para {user_type}",
    "Busca de {product} na plataforma",
    "Atualiza��o de perfil do {user_type}",
    "Pagamento com {payment_method}",
    "Adicionar {product} ao carrinho",
    "Fluxo de checkout para {user_type}",
    "Teste de API {endpoint}",
    "Valida��o de {field} no formul�rio"
]
methods = ["email", "Google", "Facebook", "Apple ID"]
platforms = ["mobile", "web", "tablet", "desktop"]
user_types = ["cliente", "admin", "convidado", "vip"]
products = ["produto", "servi�o", "assinatura", "curso"]
payment_methods = ["cart�o", "PIX", "boleto", "paypal"]
endpoints = ["/login", "/users", "/products", "/orders"]
fields = ["nome", "email", "CPF", "telefone"]

async def generate_test_data(num_records=5000):  # Reduzido de 10000 para 5000
    logger.info(f"Gerando {num_records} cen�rios de teste...")
    
    db = Database()
    faiss = FaissManager()
    
    await db.connect()
    
    BATCH_SIZE = 200
    total_generated = 0
    
    for i in range(0, num_records, BATCH_SIZE):
        batch_end = min(i + BATCH_SIZE, num_records)
        logger.info(f"Gerando cen�rios {i+1} a {batch_end}...")
        
        async with db.pool.acquire() as conn:
            for j in range(i, batch_end):
                template = random.choice(templates)
                # Preencher template com dados aleat�rios
                title = template.format(
                    method=random.choice(methods),
                    platform=random.choice(platforms),
                    user_type=random.choice(user_types),
                    product=random.choice(products),
                    payment_method=random.choice(payment_methods),
                    endpoint=random.choice(endpoints),
                    field=random.choice(fields)
                )
                # Criar descri��o relacionada
                description = f"Cen�rio de teste para {title.lower()}"
                # Gerar embedding e salvar
                embedding = faiss.model.encode([title])[0]
                await conn.execute(
                    "INSERT INTO scenarios (title, description, embedding) VALUES ($1, $2, $3)",
                    title, description, embedding
                )
                total_generated += 1
                
                if total_generated % 500 == 0:
                    logger.info(f"Gerados {total_generated}/{num_records} cen�rios")
    
    logger.info(f"Gera��o de dados conclu�da! Total: {total_generated} cen�rios")
    return total_generated

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(generate_test_data(5000))
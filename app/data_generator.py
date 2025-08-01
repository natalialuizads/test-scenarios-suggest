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
import requests
import time

BASE_URL = "http://localhost:5000"

def run_test():
    print("--- 1. Criando um Leilão ---")
    payload_create = {
        "title": "Macbook Pro M3",
        "description": "Novo, na caixa",
        "initial_price": 5000.00,
        "end_time": "2025-12-30T23:59:00", # Data futura
        "user": "Vendedor01"
    }
    r = requests.post(f"{BASE_URL}/create-auction", json=payload_create)
    print(f"Status: {r.status_code}")
    print(f"Resposta: {r.json()}")
    
    if r.status_code != 201:
        print("Erro ao criar. Abortando.")
        return

    auction_id = r.json()['id']
    
    print(f"\n--- 2. Listando Leilões Ativos ---")
    r = requests.get(f"{BASE_URL}/view-auctions")
    print(f"Leilões encontrados: {len(r.json())}")
    print(r.json())

    print(f"\n--- 3. Dando um Lance (Usuário João) ---")
    payload_bid = {
        "auction_id": auction_id,
        "user": "Joao",
        "amount": 5500.00
    }
    r = requests.post(f"{BASE_URL}/place-bid", json=payload_bid)
    print(f"Resposta: {r.json()}")

    print(f"\n--- 4. Tentando lance menor (Erro esperado) ---")
    payload_fail = {
        "auction_id": auction_id,
        "user": "Maria",
        "amount": 5100.00
    }
    r = requests.post(f"{BASE_URL}/place-bid", json=payload_fail)
    print(f"Resposta (deve ser erro): {r.json()}")

    print(f"\n--- 5. Detalhes finais do Leilão ---")
    r = requests.get(f"{BASE_URL}/auction/{auction_id}")
    print(r.json())

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"Erro: O servidor está rodando? {e}")
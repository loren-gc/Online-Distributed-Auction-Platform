import threading
import requests

# Ajuste se necessário
URL = "http://localhost:5000/place-bid"
AUCTION_ID = 1  # <--- COLOQUE O ID DO LEILÃO AQUI
BASE_PRICE = 500000000 # Preço atual do leilão

def dar_lance(i):
    # Todos tentam dar EXATAMENTE O MESMO LANCE ao mesmo tempo
    lance = BASE_PRICE + 10 
    payload = {"auction_id": AUCTION_ID, "user": f"Bot-{i}", "amount": lance}
    
    try:
        r = requests.post(URL, json=payload)
        print(f"Bot-{i}: {r.json()['message']}")
    except:
        print("Erro de conexão")

threads = []
print(f"--- Iniciando ataque de lances simultâneos no leilão {AUCTION_ID} ---")

# Cria 20 robôs tentando dar o mesmo lance
for i in range(5):
    t = threading.Thread(target=dar_lance, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
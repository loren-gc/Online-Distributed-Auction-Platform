from flask import Flask, request, jsonify
from flask_cors import CORS 
import threading
import time
import json
import os
from datetime import datetime

# Imports corrigidos (sem 'app.')
from utils.Auction import Auction
from db.redis_conn import get_redis_connection

app = Flask(__name__)
# Configuração permissiva do CORS para evitar erros no frontend
CORS(app, resources={r"/*": {"origins": "*"}})

r = get_redis_connection()

def check_expiry():
    while True:
        try:
            if r:
                active_ids = r.smembers("active_auctions")
                for aid in active_ids:
                    key = f"auction:{aid}"
                    data = r.hgetall(key)
                    
                    if data and 'end_time' in data:
                        end_time = datetime.fromisoformat(data['end_time'])
                        if datetime.now() >= end_time:
                            lock_key = f"lock:close_auction:{aid}"
                            # Lock de 10 segundos
                            is_locked = r.set(lock_key, "locked", ex=10, nx=True)
                            
                            if is_locked:
                                print(f"--> Finalizando leilão {aid}")
                                r.hset(key, "active", 0)
                                r.srem("active_auctions", aid)
                                
                                payload = {
                                    "auction_id": aid, 
                                    "winner": data.get('highest_bidder', 'Ninguém'),
                                    "final_price": data.get('current_bid', data.get('initial_price')),
                                    "item": data.get('title', 'Item')
                                }
                                r.publish("leiloes_finalizados", json.dumps(payload))
        except Exception as e:
            print(f"Erro no worker de expiração: {e}")
        time.sleep(5)

# Inicia thread apenas se não for o reloader
if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    threading.Thread(target=check_expiry, daemon=True).start()

@app.route('/create-auction', methods=['POST'])
def create():
    data = request.json
    try:
        aid = Auction.create(
            data['title'], 
            data.get('description',''), 
            data['initial_price'], 
            data['end_time'], 
            data.get('user','Anônimo')
        )
        return jsonify({"id": aid, "message": "Leilão criado com sucesso!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/view-auctions', methods=['GET'])
def view_all():
    try:
        auctions = Auction.get_all_active()
        return jsonify(auctions), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/auction/<int:aid>', methods=['GET'])
def view_one(aid):
    details = Auction.get_details(aid)
    if details:
        return jsonify(details), 200
    return jsonify({"error": "Leilão não encontrado"}), 404

@app.route('/place-bid', methods=['POST'])
def bid():
    data = request.json
    if not data or 'auction_id' not in data or 'amount' not in data:
        return jsonify({"message": "Dados inválidos"}), 400
        
    success, msg = Auction.place_bid(data['auction_id'], data['user'], data['amount'])
    status = 200 if success else 400
    return jsonify({"message": msg, "success": success}), status

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
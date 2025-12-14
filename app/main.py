from flask import Flask, request, jsonify
from app.utils.Auction import Auction
from app.db.redis_conn import get_redis_connection
import threading
import time
import json
from datetime import datetime

app = Flask(__name__)
r = get_redis_connection()

# worker interno
def check_expiry():
    """ Verifica periodicamente se leilões acabaram """
    while True:
        if r:
            active_ids = r.smembers("active_auctions")
            for aid in active_ids:
                key = f"auction:{aid}"
                data = r.hgetall(key)
                if data:
                    end_time = datetime.fromisoformat(data['end_time'])
                    if datetime.now() >= end_time:
                        print(f"--> Finalizando leilão {aid}")
                        r.hset(key, "active", 0)
                        r.srem("active_auctions", aid) #removo
                        
                        # faço em json para poder ser usado pelo agente ia
                        payload = {
                            "auction_id": aid, 
                            "winner": data['highest_bidder'],
                            "final_price": data['current_bid'],
                            "item": data['title']
                        }
                        r.publish("leiloes_finalizados", json.dumps(payload))
        time.sleep(5)

# Iinicia as threads
threading.Thread(target=check_expiry, daemon=True).start()

# rotas de post e get (criar um leilão, fazer um lance, ver os lances disponiveis e detalhes de um, se prcisar)
@app.route('/create-auction', methods=['POST'])
def create():
    data = request.json
    try:
        aid = Auction.create(
            data['title'], data.get('description',''), 
            data['initial_price'], data['end_time'], data.get('user','anon')
        )
        return jsonify({"id": aid, "msg": "Criado com sucesso"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/view-auctions', methods=['GET'])
def view_all():
    return jsonify(Auction.get_all_active())

@app.route('/auction/<int:aid>', methods=['GET'])
def view_one(aid):
    details = Auction.get_details(aid)
    return jsonify(details) if details else (jsonify({"error": "404"}), 404)

@app.route('/place-bid', methods=['POST'])
def bid():
    data = request.json
    success, msg = Auction.place_bid(data['auction_id'], data['user'], data['amount'])
    status = 200 if success else 400
    return jsonify({"message": msg}), status

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
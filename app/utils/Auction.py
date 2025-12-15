import json
import time
from db.redis_conn import get_redis_connection 

r = get_redis_connection()

class Auction:
    @staticmethod
    def create(title, description, initial_price, end_time_str, created_by):
        auction_id = r.incr("global:auction_id")
        key = f"auction:{auction_id}"

        auction_data = {
            "id": auction_id,
            "title": title,
            "description": description,
            "current_bid": initial_price,
            "initial_price": initial_price,
            "created_by": created_by,
            "end_time": end_time_str,
            "active": 1,
            "highest_bidder": "Ninguém"
        }

        r.hset(key, mapping=auction_data)
        r.sadd("active_auctions", auction_id)
        return auction_id

    @staticmethod
    def get_all_active():
        active_ids = r.smembers("active_auctions")
        auctions = []
        for aid in active_ids:
            data = r.hgetall(f"auction:{aid}")
            if data:
                auctions.append(data)
        return auctions

    @staticmethod
    def get_details(auction_id):
        key = f"auction:{auction_id}"
        data = r.hgetall(key)
        if not data:
            return None

        raw_bids = r.zrevrange(f"{key}:bids", 0, 9, withscores=True)
        bids = []
        for member, score in raw_bids:
            bids.append(json.loads(member))

        data['bids_history'] = bids
        return data

    @staticmethod
    def place_bid(auction_id, user, bid_amount):
        key = f"auction:{auction_id}"
        try:
            with r.pipeline() as pipe:
                while True:
                    try:
                        pipe.watch(key)
                        auction_data = pipe.hgetall(key)
                        if not auction_data:
                            return False, "Leilão não encontrado."

                        if str(auction_data['active']) == '0':
                            return False, "Leilão encerrado."

                        current_bid = float(auction_data['current_bid'])
                        bid_amount = float(bid_amount)

                        if bid_amount <= current_bid:
                            pipe.unwatch()
                            return False, f"Lance deve ser maior que {current_bid}"

                        pipe.multi()
                        pipe.hset(key, mapping={
                            "current_bid": bid_amount,
                            "highest_bidder": user
                        })

                        bid_info = json.dumps({
                            "user": user,
                            "amount": bid_amount,
                            "time": time.time()
                        })
                        pipe.zadd(f"{key}:bids", {bid_info: bid_amount})
                        pipe.execute()

                        msg = json.dumps({
                            "auction_id": auction_id,
                            "new_bid": bid_amount,
                            "winner": user
                        })
                        r.publish("auction_updates", msg)

                        return True, "Lance aceito!"

                    except r.WatchError:
                        continue
        except Exception as e:
            return False, str(e)
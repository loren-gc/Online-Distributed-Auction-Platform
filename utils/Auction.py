# Lorenzo Grippo Chiachio - 823917
# João Vitor Seiji - 822767

import time
import json
from app.db.redis_conn import get_redis_connection

# Conexão única com o Redis (compartilhada entre os Pods)
r = get_redis_connection()


class Auction:
    '''
    Classe refatorada para persistência no Redis.

    A classe possui os atributos:
        auctionId (int)
        currentBid (double ou float)
        title / description (string)
        active (boolean representado por 0 ou 1)
        highest_bidder (string)

    Gerencia a lógica de criação, listagem e lances em um ambiente distribuído.
    '''

    @staticmethod
    # usamos método estático para ler e escrever no Redis,
    # assim qualquer instância (Pod) acessa os mesmos dados
    def create(title, description, initial_price, end_time_str, created_by):
        """ 
        Cria um novo leilão no Redis 
        """

        # cria um novo leilão com ID atômico
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
            "active": 1,  # 1 = ativo, 0 = encerrado
            "highest_bidder": "Ninguém"
        }

        # salva os dados do leilão no Redis (Hash)
        r.hset(key, mapping=auction_data)

        # adiciona o ID do leilão no conjunto de leilões ativos
        r.sadd("active_auctions", auction_id)

        return auction_id

    @staticmethod
    def get_all_active():
        # busca todos os leilões ativos
        active_ids = r.smembers("active_auctions")
        auctions = []

        for aid in active_ids:
            data = r.hgetall(f"auction:{aid}")
            if data:
                auctions.append(data)

        return auctions

    @staticmethod
    def get_details(auction_id):
        # busca detalhes do leilão e histórico de lances
        key = f"auction:{auction_id}"
        data = r.hgetall(key)

        if not data:
            return None

        # busca os últimos 10 lances (Sorted Set)
        raw_bids = r.zrevrange(f"{key}:bids", 0, 9, withscores=True)
        bids = []

        for member, score in raw_bids:
            bids.append(json.loads(member))

        data['bids_history'] = bids
        return data

    @staticmethod
    def place_bid(auction_id, user, bid_amount):
        # realiza um lance com transação segura

        key = f"auction:{auction_id}"

        try:
            # uso de pipeline para garantir atomicidade,
            # já que podemos ter lances simultâneos em múltiplos Pods
            with r.pipeline() as pipe:
                while True:
                    try:
                        # monitora a chave para detectar mudanças concorrentes
                        pipe.watch(key)

                        auction_data = pipe.hgetall(key)
                        if not auction_data:
                            return False, "Leilão não encontrado."

                        if str(auction_data['active']) == '0':
                            return False, "Leilão encerrado."

                        current_bid = float(auction_data['current_bid'])
                        bid_amount = float(bid_amount)

                        # o lance que foi dado deve ser maior que o atual
                        if bid_amount <= current_bid:
                            pipe.unwatch()
                            return False, f"Lance deve ser maior que {current_bid}"

                        # se passar nas verificações, prepara a transação
                        pipe.multi()
                        pipe.hset(key, mapping={
                            "current_bid": bid_amount,
                            "highest_bidder": user
                        })

                        # adiciona o lance ao histórico (Sorted Set)
                        bid_info = json.dumps({
                            "user": user,
                            "amount": bid_amount,
                            "time": time.time()
                        })
                        pipe.zadd(f"{key}:bids", {bid_info: bid_amount})

                        # executa a transação
                        pipe.execute()

                        # publica o evento para atualização em tempo real (Pub/Sub)
                        msg = json.dumps({
                            "auction_id": auction_id,
                            "new_bid": bid_amount,
                            "winner": user
                        })
                        r.publish("auction_updates", msg)

                        return True, "Lance aceito!"

                    except r.WatchError:
                        # se houver conflito (outro lance simultâneo),
                        # tenta novamente o loop
                        continue

        except Exception as e:
            return False, str(e)

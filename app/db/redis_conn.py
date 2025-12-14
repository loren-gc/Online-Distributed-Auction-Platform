import redis
import os

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')#define onde redis está rodadando
REDIS_PORT = int (os.getenv('REDIS_PORT', 6379))#uso a porta padrão
REDIS_DB = int (os.getenv('REDIS_DB', 0))#banco lógico do redis que será usado

def get_redis_connection():#função para criar uma conexão com redis
    try:
        r = redis.Redis(host=REDIS_HOST,
                        port =REDIS_PORT,
                        DB=REDIS_DB,
                        decode_responses=True)#recebo strings e nao bytes
        return r
    except Exception as e:
        print(f"Erro ao conectar no Redis: {e}")
        return None

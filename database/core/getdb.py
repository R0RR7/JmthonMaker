import os
import sys
import logging
from jmthon.config import Var
from .base import BaseDatabase

Redis = MongoClient = psycopg2 = Database = None
LOGS = logging.getLogger("Jmthon")

if Var.REDIS_URI or Var.REDISHOST:
    try:
        from redis import Redis
    except ImportError:
        LOGS.info("Installing 'redis' for database.")
        os.system(f"{sys.executable} -m pip install -q redis hiredis")
        from redis import Redis

elif Var.MONGO_URI:
    try:
        from pymongo import MongoClient
    except ImportError:
        LOGS.info("Installing 'pymongo' for database.")
        os.system(f"{sys.executable} -m pip install -q pymongo[srv]")
        from pymongo import MongoClient

elif Var.DATABASE_URL:
    try:
        import psycopg2
        from psycopg2 import pool
    except ImportError:
        LOGS.info("Installing 'pyscopg2' for database.")
        os.system(f"{sys.executable} -m pip install -q psycopg2-binary")
        import psycopg2
        from psycopg2 import pool

else:
    try:
        from .local import Database as localdb_
    except ImportError:
        LOGS.info("Using local file as database.")
        os.system("pip3 install -q localdb.json")
        from local import Database as localdb_

class MongoDB(BaseDatabase):
    def __init__(self, key, dbname="pyDatabase"):
        self.dB = MongoClient(key, serverSelectionTimeoutMS=5000)
        self.db = self.dB[dbname]
        super().__init__()

    def __repr__(self):
        return f"<Jmthon.MonGoDB\n -total_keys: {len(self.keys())}\n>"

    @property
    def name(self):
        return "MONGO"

    @property
    def usage(self):
        return self.db.command("dbstats")["dataSize"]

    def ping(self):
        if self.dB.server_info():
            return True

    def keys(self):
        return self.db.list_collection_names()

    def set(self, key, value):
        if key in self.keys():
            self.db[key].replace_one({"_id": key}, {"value": str(value)})
        else:
            self.db[key].insert_one({"_id": key, "value": str(value)})
        return True

    def delete(self, key):
        self.db.drop_collection(key)

    def get(self, key):
        if x := self.db[key].find_one({"_id": key}):
            return x["value"]

    def flushall(self):
        self.dB.drop_database("pyDatabase")
        self._cache.clear()
        return True



class SqlDB(BaseDatabase):
    def __init__(self, dbUrl: str, dBname='Jmthon'):
        self.pool = pool.SimpleConnectionPool(
            1, 3, dsn=dbUrl, sslmode='require')
        self.pool_conn = self.pool.getconn()
        self.pool_cursor = self.pool_conn.cursor()
        self.pool_conn.autocommit = True
        self.pool_cursor.execute(
            "CREATE TABLE IF NOT EXISTS Jmthon (jmthonCli varchar(70))")
        super().__init__()

    def __repr__(self):
        return f"<Jmthon.PostgreSQL\n -total_keys: {len(self.keys())}\n>"

    @property
    def name(self):
        return "postgreSQL"

    @property
    def usage(self):
        self.pool_cursor.execute(
            "SELECT pg_size_pretty(pg_relation_size('Jmthon')) AS size")
        data = self.pool_cursor.fetchall()
        return int(data[0][0].split()[0])

    def keys(self):
        self.pool_cursor.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name  = 'jmthon'")  # case sensitive
        data = self.pool_cursor.fetchall()
        return [_[0] for _ in data]

    def set(self, key, value):
        try:
            self.pool_cursor.execute(
                f"ALTER TABLE Jmthon DROP COLUMN IF EXISTS {key}")
        except (psycopg2.errors.UndefinedColumn, psycopg2.errors.SyntaxError):
            pass
        except BaseException as er:
            LOGS.exception(er)
        self._cache.update({key: value})
        self.pool_cursor.execute(f"ALTER TABLE Jmthon ADD {key} TEXT")
        self.pool_cursor.execute(
            f"INSERT INTO Jmthon ({key}) values (%s)", (str(value),))
        return True

    def delete(self, key):
        try:
            self.pool_cursor.execute(f"ALTER TABLE Jmthon DROP COLUMN {key}")
        except psycopg2.errors.UndefinedColumn:
            return False
        return True

    def get(self, variable):
        try:
            self.pool_cursor.execute(f"SELECT {variable} FROM Jmthon")
        except psycopg2.errors.UndefinedColumn:
            return None
        data = self.pool_cursor.fetchall()
        if not data:
            return None
        if len(data) >= 1:
            for i in data:
                if i[0]:
                    return i[0]

    def flushall(self):
        self._cache.clear()
        self.pool_cursor.execute("DROP TABLE Jmthon")
        self.pool_cursor.execute(
            "CREATE TABLE IF NOT EXISTS Jmthon (jmthonCli varchar(70))")
        return True


class RedisDB(BaseDatabase):
    def __init__(self, host, port, password, logger=LOGS, *args, **kwargs):
        if host and ":" in host:
            spli_ = host.split(":")
            host = spli_[0]
            port = int(spli_[-1])
            if host.startswith("http"):
                logger.error("Your REDIS_URI should not start with http !")
                import sys
                sys.exit()
        elif not host or not port:
            logger.error("Port Number not found")
            import sys
            sys.exit()
        kwargs["host"] = host
        kwargs["password"] = password
        kwargs["port"] = port

        self.db = Redis(**kwargs)
        self.set = self.db.set
        self.get = self.db.get
        self.keys = self.db.keys
        self.delete = self.db.delete
        super().__init__()

    @property
    def name(self):
        return "REDIS"

    @property
    def usage(self):
        return sum(self.db.memory_usage(x) for x in self.keys())

class LocalDB(BaseDatabase):
    def __init__(self, dbname="JmthonDB"):
        self.dB = localdb_(database_name=dbname)
        super().__init__()

    def __repr__(self):
        return f"<Jmthon.LocalDB\n -total_keys: {len(self.keys())}\n>"

    @property
    def name(self):
        return "Local"

    @property
    def usage(self):
        return self.dB.size

    def keys(self):
        return self.dB._cache.keys()

    def set(self, key, value):
        return self.dB.set(key, value)

    def delete(self, key):
        return self.dB.delete(key)

    def get(self, key):
        return self.dB.get(key)

    def flushall(self):
        for key in self.keys():
            self.dB.delete(key)
        return True

def pyDatabase():
    _er = False
    try:
        if Redis:
            return RedisDB(
                host=Var.REDIS_URI or Var.REDISHOST,
                password=Var.REDIS_PASSWORD,
                port=Var.REDISPORT,
                decode_responses=True,
                socket_timeout=5,
                retry_on_timeout=True,
            )
        if MongoClient:
            return MongoDB(Var.MONGO_URI)
        if psycopg2:
            return SqlDB(Var.DATABASE_URL)
    except BaseException as err:
        LOGS.exception(err)
        _er = True
    if not _er:
        LOGS.critical(
            "No DB requirement fullfilled!\nnow use local db."
        )
        return LocalDB()
    exit()


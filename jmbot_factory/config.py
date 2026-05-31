import os
from decouple import Config, RepositoryEnv

FACTORY_DIR = os.path.dirname(os.path.abspath(__file__))
_env_file = os.path.join(FACTORY_DIR, ".env")
_config = Config(RepositoryEnv(_env_file))

API_ID = _config("API_ID", cast=int)
API_HASH = _config("API_HASH")
BOT_TOKEN = _config("BOT_TOKEN")
OWNER_ID = _config("OWNER_ID", cast=int, default=0)
SUPPORT_USERNAME = _config("SUPPORT_USERNAME", default="DEV_USERNAME")

MASTER_DIR = os.path.dirname(FACTORY_DIR)
DEPLOY_DIR = os.path.join(FACTORY_DIR, "deployments")

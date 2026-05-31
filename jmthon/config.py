import os
from decouple import AutoConfig
from ast import literal_eval

version = "1.0.0"

_config = AutoConfig(search_path=os.getcwd())

class Config:
    def __getattr__(self, __name: str):
        if __name in self.__dict__:
            return self.__dict__[__name]
        _data = _config(__name, default="")
        try:
            return literal_eval(_data)
        except Exception:
            return _data

    API_ID = _config("API_ID", cast=int, default=6)
    API_HASH = _config("API_HASH", default="eb06d4abfb49dc3eeb1aeb98ae0f581e")

Var = Config = Config()

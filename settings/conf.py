from pathlib import Path

from decouple import AutoConfig, Csv

SETTINGS_DIR=Path(__file__).resolve().parent
config=AutoConfig(search_path=SETTINGS_DIR)

ENV_ID: str=config("BLOG_ENV_ID", default= "local")
SECRET_KEY: str=config("BLOG_SECRET_KEY")
ALLOWED_HOSTS: list[str]=config("BLOG_ALLOWED_HOSTS", default="", cast=Csv())

DB_NAME:str=config("BLOG_DB_NAME", default="")
DB_USER:str=config("BLOG_DB_USER", default="")
DB_PASSWORD: str= config("BLOG_DB_PASSWORD", default="")
DB_HOST:str=config("BLOG_DB_HOST", default="localhost")
DB_PORT: str=config("BLOG_DB_PORT", default="5432")

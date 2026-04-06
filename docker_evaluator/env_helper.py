from dotenv import load_dotenv
import os

def load_env_variables():
    load_dotenv(".env")
    load_dotenv(f".env.{os.getenv('ENVIRONMENT')}")

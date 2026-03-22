
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
env_path = os.path.join(project_root, ".env")

class Settings(BaseSettings):
    DATABASE_HOSTNAME: str
    DATABASE_PORT: int
    DATABASE_PASSWORD: str
    DATABASE_NAME: str
    DATABASE_USERNAME: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    OPENAI_API_KEY: str
    LANGCHAIN_API_KEY: str
    LANGCHAIN_PROJECT: str
    
    model_config = SettingsConfigDict(
        env_file=env_path,
        extra="ignore"
    )
 
settings = Settings()
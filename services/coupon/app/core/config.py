from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str
    pg_pool_size: int = 20
    redis_pool_size: int = 64
    grpc_port: int = 50051

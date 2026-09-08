from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_src: str | None = None
    test_db_src: str | None = None
    testing: bool = False

    @property
    def db_url(self):
        if self.testing and self.test_db_src:
            return self.test_db_src
        else:
            return self.db_src

settings = Settings()
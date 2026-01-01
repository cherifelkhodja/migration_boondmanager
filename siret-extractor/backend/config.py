"""Configuration module for the SIRET extractor backend."""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API INSEE SIRENE
    insee_api_key: str = ""
    insee_base_url: str = "https://api.insee.fr/api-sirene/3.11"
    insee_rate_limit: int = 30  # requests per period
    insee_rate_period: int = 60  # seconds

    # API RNE (INPI)
    rne_jwt_token: str = ""
    rne_base_url: str = "https://registre-national-entreprises.inpi.fr/api"

    # Backend settings
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Redis (optional)
    redis_url: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Mapping des categories juridiques vers formes juridiques
FORMES_JURIDIQUES = {
    "1000": "EI",
    "1100": "EI",
    "1200": "EI",
    "1300": "EI",
    "5498": "EURL",
    "5499": "SARL",
    "5505": "SA",
    "5510": "SA",
    "5515": "SA",
    "5520": "SA",
    "5522": "SA",
    "5525": "SA",
    "5530": "SA",
    "5531": "SA",
    "5532": "SA",
    "5538": "SA",
    "5539": "SA",
    "5543": "SA",
    "5546": "SA",
    "5547": "SA",
    "5548": "SA",
    "5551": "SA",
    "5552": "SA",
    "5553": "SA",
    "5554": "SA",
    "5555": "SA",
    "5558": "SA",
    "5559": "SA",
    "5560": "SA",
    "5570": "SAS",
    "5571": "SAS",
    "5572": "SAS",
    "5585": "SAS",
    "5588": "SAS",
    "5589": "SAS",
    "5599": "SAS",
    "5605": "SAS",
    "5610": "SAS",
    "5615": "SAS",
    "5699": "SAS",
    "5710": "SAS",
    "5720": "SASU",
    "5785": "SAS",
    "5800": "SAS",
}

# Mapping des roles RNE vers fonctions lisibles
ROLES_MAPPING = {
    "PRESIDENT": "President",
    "GERANT": "Gerant",
    "DIRECTEUR_GENERAL": "Directeur General",
    "ASSOCIE_UNIQUE": "Associe Unique",
    "ADMINISTRATEUR": "Administrateur",
    "PRESIDENT_DU_CONSEIL_D_ADMINISTRATION": "President du CA",
    "PRESIDENT_DU_CONSEIL_DE_SURVEILLANCE": "President du CS",
    "MEMBRE": "Membre",
    "MEMBRE_DU_CONSEIL_D_ADMINISTRATION": "Membre du CA",
    "MEMBRE_DU_CONSEIL_DE_SURVEILLANCE": "Membre du CS",
    "DIRECTEUR_GENERAL_DELEGUE": "Directeur General Delegue",
    "COMMISSAIRE_AUX_COMPTES": "Commissaire aux Comptes",
    "ASSOCIE": "Associe",
    "LIQUIDATEUR": "Liquidateur",
}

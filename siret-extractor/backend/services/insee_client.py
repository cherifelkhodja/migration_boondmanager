"""Client for INSEE SIRENE API."""
import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta
import httpx

from config import get_settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, max_calls: int, period: int):
        """Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed in period
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls: list[datetime] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until a call can be made within rate limits."""
        async with self._lock:
            now = datetime.now()
            # Remove calls outside the current period
            self.calls = [
                call for call in self.calls
                if now - call < timedelta(seconds=self.period)
            ]

            if len(self.calls) >= self.max_calls:
                # Wait until the oldest call expires
                oldest = self.calls[0]
                wait_time = (oldest + timedelta(seconds=self.period) - now).total_seconds()
                if wait_time > 0:
                    logger.info(f"Rate limit reached, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)

            self.calls.append(datetime.now())


class INSEEClient:
    """Client for interacting with INSEE SIRENE API."""

    def __init__(self):
        """Initialize INSEE client with settings."""
        self.settings = get_settings()
        self.base_url = self.settings.insee_base_url
        self.headers = {
            "X-INSEE-Api-Key-Integration": self.settings.insee_api_key,
            "Accept": "application/json",
        }
        self.rate_limiter = RateLimiter(
            max_calls=self.settings.insee_rate_limit,
            period=self.settings.insee_rate_period,
        )

    async def get_etablissement(self, siret: str) -> Optional[dict]:
        """Get establishment data by SIRET.

        Args:
            siret: 14-digit SIRET number

        Returns:
            Dictionary with establishment data or None if not found
        """
        await self.rate_limiter.acquire()

        async with httpx.AsyncClient(timeout=30) as client:
            for attempt in range(3):
                try:
                    response = await client.get(
                        f"{self.base_url}/siret/{siret}",
                        headers=self.headers,
                    )

                    if response.status_code == 200:
                        data = response.json()
                        return data.get("etablissement")
                    elif response.status_code == 404:
                        logger.warning(f"SIRET {siret} not found in INSEE")
                        return None
                    elif response.status_code == 429:
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            f"INSEE API error for {siret}: {response.status_code} - {response.text}"
                        )
                        return None
                except httpx.TimeoutException:
                    wait_time = 2 ** attempt
                    logger.warning(f"Timeout for {siret}, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                except Exception as e:
                    logger.error(f"Error fetching {siret}: {e}")
                    return None

        return None

    async def get_unite_legale(self, siren: str) -> Optional[dict]:
        """Get legal unit data by SIREN.

        Args:
            siren: 9-digit SIREN number

        Returns:
            Dictionary with legal unit data or None if not found
        """
        await self.rate_limiter.acquire()

        async with httpx.AsyncClient(timeout=30) as client:
            for attempt in range(3):
                try:
                    response = await client.get(
                        f"{self.base_url}/siren/{siren}",
                        headers=self.headers,
                    )

                    if response.status_code == 200:
                        data = response.json()
                        return data.get("uniteLegale")
                    elif response.status_code == 404:
                        logger.warning(f"SIREN {siren} not found in INSEE")
                        return None
                    elif response.status_code == 429:
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            f"INSEE API error for {siren}: {response.status_code}"
                        )
                        return None
                except httpx.TimeoutException:
                    wait_time = 2 ** attempt
                    logger.warning(f"Timeout for {siren}, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                except Exception as e:
                    logger.error(f"Error fetching {siren}: {e}")
                    return None

        return None

    def extract_data(self, etablissement: dict, unite_legale: dict = None) -> dict:
        """Extract relevant data from INSEE API response.

        Args:
            etablissement: Establishment data from API
            unite_legale: Optional legal unit data for additional info

        Returns:
            Dictionary with extracted company data
        """
        result = {
            "siret": "",
            "siren": "",
            "raison_sociale": "",
            "adresse": "",
            "code_postal": "",
            "ville": "",
            "code_ape": "",
            "categorie_juridique": "",
        }

        if not etablissement:
            return result

        # Basic identification
        result["siret"] = etablissement.get("siret", "")
        result["siren"] = etablissement.get("siren", "")

        # Address from adresseEtablissement
        adresse = etablissement.get("adresseEtablissement", {})
        if adresse:
            # Build full address
            parts = []
            if adresse.get("numeroVoieEtablissement"):
                parts.append(adresse["numeroVoieEtablissement"])
            if adresse.get("indiceRepetitionEtablissement"):
                parts.append(adresse["indiceRepetitionEtablissement"])
            if adresse.get("typeVoieEtablissement"):
                parts.append(adresse["typeVoieEtablissement"])
            if adresse.get("libelleVoieEtablissement"):
                parts.append(adresse["libelleVoieEtablissement"])

            result["adresse"] = " ".join(parts)
            result["code_postal"] = adresse.get("codePostalEtablissement", "")
            result["ville"] = adresse.get("libelleCommuneEtablissement", "")

        # Current period data
        periodes = etablissement.get("periodesEtablissement", [])
        if periodes:
            # Get most recent period (first in list)
            current = periodes[0]
            result["code_ape"] = current.get("activitePrincipaleEtablissement", "")

        # Legal unit data
        ul = etablissement.get("uniteLegale", {}) or unite_legale or {}
        if ul:
            # Get current period for legal unit
            periodes_ul = ul.get("periodesUniteLegale", [])
            if periodes_ul:
                current_ul = periodes_ul[0]

                # Raison sociale - different for EI vs companies
                denomination = current_ul.get("denominationUniteLegale", "")
                if denomination:
                    result["raison_sociale"] = denomination
                else:
                    # EI: use nom + prenom
                    nom = current_ul.get("nomUniteLegale", "")
                    prenom = current_ul.get("prenomUsuelUniteLegale", "")
                    if nom:
                        result["raison_sociale"] = f"{prenom} {nom}".strip()

                result["categorie_juridique"] = current_ul.get(
                    "categorieJuridiqueUniteLegale", ""
                )

        return result

"""Client for RNE (Registre National des Entreprises) API from INPI."""
import asyncio
import logging
from typing import Optional
import httpx

from config import get_settings, ROLES_MAPPING

logger = logging.getLogger(__name__)


def get_first_prenom(prenoms) -> str:
    """Extract first prenom from string or list."""
    if not prenoms:
        return ""
    if isinstance(prenoms, list):
        return prenoms[0] if prenoms else ""
    if isinstance(prenoms, str):
        return prenoms.split()[0] if prenoms else ""
    return str(prenoms)


class RNEClient:
    """Client for interacting with RNE INPI API."""

    BASE_URL = "https://registre-national-entreprises.inpi.fr/api"

    def __init__(self):
        """Initialize RNE client with settings."""
        self.settings = get_settings()
        self.token = self.settings.rne_jwt_token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }

    async def get_company(self, siren: str) -> Optional[dict]:
        """Get company data from RNE by SIREN.

        Args:
            siren: 9-digit SIREN number

        Returns:
            Dictionary with company data or None if not found
        """
        async with httpx.AsyncClient(timeout=30) as client:
            for attempt in range(3):
                try:
                    response = await client.get(
                        f"{self.BASE_URL}/companies/{siren}",
                        headers=self.headers,
                    )

                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 401:
                        logger.error("RNE API: Token expired or invalid")
                        return None
                    elif response.status_code == 404:
                        logger.warning(f"SIREN {siren} not found in RNE")
                        return None
                    elif response.status_code == 429:
                        wait_time = 2 ** attempt
                        logger.warning(f"RNE rate limited, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            f"RNE API error for {siren}: {response.status_code} - {response.text[:200]}"
                        )
                        return None
                except httpx.TimeoutException:
                    wait_time = 2 ** attempt
                    logger.warning(f"RNE timeout for {siren}, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                except Exception as e:
                    logger.error(f"Error fetching {siren} from RNE: {e}")
                    return None

        return None

    def extract_capital(self, data: dict) -> str:
        """Extract capital social from RNE data.

        Args:
            data: Full RNE API response

        Returns:
            Formatted capital string (e.g., "50 000,00") or empty string
        """
        try:
            # Try personneMorale path
            capital_info = (
                data.get("formality", {})
                .get("content", {})
                .get("personneMorale", {})
                .get("identite", {})
                .get("description", {})
                .get("capitalSocial", {})
            )

            if capital_info:
                montant = capital_info.get("montant", 0)
                if montant:
                    # Format with spaces as thousands separator and comma for decimals
                    formatted = f"{montant:,.2f}".replace(",", " ").replace(".", ",")
                    # Fix the space placement (from 50,000.00 style to 50 000,00)
                    return formatted.replace(" ", " ")

            # Alternative path: check identite directly
            identite = (
                data.get("formality", {})
                .get("content", {})
                .get("personneMorale", {})
                .get("identite", {})
            )
            if identite:
                capital_info = identite.get("description", {}).get("capitalSocial", {})
                if capital_info:
                    montant = capital_info.get("montant", 0)
                    if montant:
                        formatted = f"{montant:,.2f}".replace(",", " ").replace(".", ",")
                        return formatted

        except (KeyError, TypeError) as e:
            logger.debug(f"Could not extract capital: {e}")

        return ""

    def extract_dirigeant_principal(self, data: dict) -> dict:
        """Extract the main director from RNE data.

        Priority order: President > Gerant > DG > Associe Unique > First in list

        Args:
            data: Full RNE API response

        Returns:
            Dictionary with nom, prenom, fonction, civilite
        """
        default = {"nom": "", "prenom": "", "fonction": "", "civilite": ""}

        try:
            # Get pouvoirs list
            pouvoirs = (
                data.get("formality", {})
                .get("content", {})
                .get("personneMorale", {})
                .get("composition", {})
                .get("pouvoirs", [])
            )

            if not pouvoirs:
                # Try alternative path for some company types
                pouvoirs = (
                    data.get("formality", {})
                    .get("content", {})
                    .get("personnePhysique", {})
                    .get("identite", {})
                )
                if pouvoirs:
                    # This is an EI - extract entrepreneur info
                    entrepreneur = pouvoirs.get("entrepreneur", {})
                    descr = entrepreneur.get("descriptionPersonne", {})
                    return {
                        "nom": descr.get("nom", ""),
                        "prenom": get_first_prenom(descr.get("prenoms")),
                        "fonction": "Entrepreneur Individuel",
                        "civilite": self._determine_civilite(descr),
                    }
                return default

            # Priority of roles
            priority = ["PRESIDENT", "GERANT", "DIRECTEUR_GENERAL", "ASSOCIE_UNIQUE"]

            # Search by priority
            for role in priority:
                for p in pouvoirs:
                    if (
                        p.get("roleEntreprise") == role
                        and p.get("typeDePersonne") == "PERSONNE_PHYSIQUE"
                    ):
                        individu = p.get("individu", {})
                        descr = individu.get("descriptionPersonne", {})
                        return {
                            "nom": descr.get("nom", ""),
                            "prenom": get_first_prenom(descr.get("prenoms")),
                            "fonction": self._map_role(role),
                            "civilite": self._determine_civilite(descr),
                        }

            # Fallback: first person in list
            for p in pouvoirs:
                if p.get("typeDePersonne") == "PERSONNE_PHYSIQUE":
                    individu = p.get("individu", {})
                    descr = individu.get("descriptionPersonne", {})
                    role = p.get("roleEntreprise", "")
                    return {
                        "nom": descr.get("nom", ""),
                        "prenom": get_first_prenom(descr.get("prenoms")),
                        "fonction": self._map_role(role),
                        "civilite": self._determine_civilite(descr),
                    }

                elif p.get("typeDePersonne") == "PERSONNE_MORALE":
                    # Corporate director
                    entreprise = p.get("entreprise", {})
                    return {
                        "nom": entreprise.get("denomination", ""),
                        "prenom": "",
                        "fonction": self._map_role(p.get("roleEntreprise", "")),
                        "civilite": "",
                    }

        except (KeyError, TypeError) as e:
            logger.debug(f"Could not extract dirigeant: {e}")

        return default

    def _map_role(self, role: str) -> str:
        """Map RNE role code to readable function name."""
        if not role:
            return ""
        return ROLES_MAPPING.get(role, role.replace("_", " ").title())

    def _determine_civilite(self, description: dict) -> str:
        """Determine civilite (M/Mme) from person description.

        Args:
            description: descriptionPersonne dict from RNE

        Returns:
            "M" or "Mme" or empty string
        """
        # Check if sexe field is available
        sexe = description.get("sexe", "")
        if sexe:
            if sexe.upper() in ("M", "MASCULIN", "H", "HOMME"):
                return "M"
            elif sexe.upper() in ("F", "FEMININ", "FEMME"):
                return "Mme"

        # Fallback: try to guess from first name
        prenom = get_first_prenom(description.get("prenoms")).lower()

        # Common French feminine first names endings
        feminine_endings = ("e", "a", "ine", "ette", "elle", "ie")
        feminine_names = {
            "marie", "anne", "sophie", "nathalie", "isabelle", "sylvie",
            "catherine", "christine", "francoise", "valerie", "stephanie",
            "sandrine", "caroline", "celine", "aurelie", "julie", "claire",
            "sarah", "laura", "emma", "lea", "chloe", "camille", "manon",
        }

        if prenom in feminine_names:
            return "Mme"

        # Default to M (common in French business context)
        return "M"

    def extract_all(self, data: dict) -> dict:
        """Extract all relevant data from RNE response.

        Args:
            data: Full RNE API response

        Returns:
            Dictionary with capital and dirigeant info
        """
        dirigeant = self.extract_dirigeant_principal(data)
        return {
            "capital": self.extract_capital(data),
            "civilite_contact": dirigeant["civilite"],
            "nom_contact": dirigeant["nom"],
            "prenom_contact": dirigeant["prenom"],
            "fonction_contact": dirigeant["fonction"],
        }

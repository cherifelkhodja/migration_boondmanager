"""Data processor for merging INSEE and RNE data."""
import asyncio
import logging
import re
from typing import Optional

from config import FORMES_JURIDIQUES
from models.schemas import CompanyData
from .insee_client import INSEEClient
from .rne_client import RNEClient

logger = logging.getLogger(__name__)


def calc_tva_intracommunautaire(siren: str) -> str:
    """Calculate French intra-community VAT number.

    Formula: FR + key + SIREN
    Key = (12 + 3 * (SIREN % 97)) % 97

    Args:
        siren: 9-digit SIREN number

    Returns:
        VAT number in format FRXXXXXXXXXXXX
    """
    try:
        siren_int = int(siren)
        key = (12 + 3 * (siren_int % 97)) % 97
        return f"FR{key:02d}{siren}"
    except (ValueError, TypeError):
        return ""


def format_rcs(siren: str, ville: str) -> str:
    """Format RCS number.

    Args:
        siren: 9-digit SIREN number
        ville: City name

    Returns:
        Formatted RCS string like "XXX XXX XXX R.C.S. Paris"
    """
    if not siren or len(siren) != 9:
        return ""

    formatted_siren = f"{siren[:3]} {siren[3:6]} {siren[6:9]}"
    return f"{formatted_siren} R.C.S. {ville}" if ville else formatted_siren


def format_capital(montant: float) -> str:
    """Format capital amount for display.

    Args:
        montant: Capital amount as number

    Returns:
        Formatted string like "50 000,00"
    """
    if not montant:
        return ""
    # Format with French conventions
    formatted = f"{montant:,.2f}"
    # Replace comma with space for thousands, dot with comma for decimals
    formatted = formatted.replace(",", " ").replace(".", ",")
    return formatted


def get_forme_juridique(categorie_juridique: str) -> str:
    """Get legal form from category code.

    Args:
        categorie_juridique: INSEE legal category code

    Returns:
        Legal form abbreviation (SAS, SASU, SARL, etc.)
    """
    if not categorie_juridique:
        return ""

    # Direct lookup
    if categorie_juridique in FORMES_JURIDIQUES:
        return FORMES_JURIDIQUES[categorie_juridique]

    # Pattern-based fallback
    code = categorie_juridique[:2] if len(categorie_juridique) >= 2 else ""

    if code in ("10", "11", "12", "13"):
        return "EI"
    elif code == "54":
        # SARL family
        if categorie_juridique in ("5498",):
            return "EURL"
        return "SARL"
    elif code in ("57", "58"):
        # SAS family - check for single shareholder
        if categorie_juridique in ("5720",):
            return "SASU"
        return "SAS"
    elif code == "55":
        return "SA"
    elif code == "52":
        return "SNC"
    elif code == "53":
        return "SCS"
    elif code == "56":
        return "SCA"

    return categorie_juridique


def validate_siret(siret: str) -> tuple[bool, str]:
    """Validate SIRET number format.

    Args:
        siret: SIRET number to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Remove spaces and special characters
    clean = re.sub(r"[^0-9]", "", siret)

    if not clean:
        return False, "SIRET vide"

    if len(clean) != 14:
        return False, f"SIRET doit avoir 14 chiffres (recu: {len(clean)})"

    # Luhn checksum validation (optional but recommended)
    # The last digit is a checksum digit

    return True, ""


class DataProcessor:
    """Processor for extracting and merging company data."""

    def __init__(self):
        """Initialize data processor with API clients."""
        self.insee_client = INSEEClient()
        self.rne_client = RNEClient()

    async def process_siret(self, siret: str) -> CompanyData:
        """Process a single SIRET and return company data.

        Args:
            siret: 14-digit SIRET number

        Returns:
            CompanyData object with extracted information
        """
        # Validate SIRET
        is_valid, error = validate_siret(siret)
        if not is_valid:
            return CompanyData(siret=siret, erreur=error)

        # Clean SIRET
        clean_siret = re.sub(r"[^0-9]", "", siret)
        siren = clean_siret[:9]

        # Fetch data from both APIs concurrently
        insee_task = self.insee_client.get_etablissement(clean_siret)
        rne_task = self.rne_client.get_company(siren)

        insee_data, rne_data = await asyncio.gather(
            insee_task, rne_task, return_exceptions=True
        )

        # Handle exceptions
        if isinstance(insee_data, Exception):
            logger.error(f"INSEE error for {siret}: {insee_data}")
            insee_data = None

        if isinstance(rne_data, Exception):
            logger.error(f"RNE error for {siret}: {rne_data}")
            rne_data = None

        # Process results
        result = self._merge_data(clean_siret, insee_data, rne_data)
        return result

    def _merge_data(
        self,
        siret: str,
        insee_data: Optional[dict],
        rne_data: Optional[dict],
    ) -> CompanyData:
        """Merge data from INSEE and RNE APIs.

        Args:
            siret: Clean 14-digit SIRET
            insee_data: Data from INSEE API
            rne_data: Data from RNE API

        Returns:
            CompanyData with merged information
        """
        siren = siret[:9]
        donnees_partielles = False
        erreur = None

        # Initialize with defaults
        result = {
            "siret": siret,
            "raison_sociale": "",
            "rcs": "",
            "forme_juridique": "",
            "capital": "",
            "tva_intracommunautaire": "",
            "code_ape": "",
            "adresse": "",
            "code_postal": "",
            "ville": "",
            "pays": "France",
            "civilite_contact": "",
            "nom_contact": "",
            "prenom_contact": "",
            "fonction_contact": "",
        }

        # Handle case where neither API returned data
        if not insee_data and not rne_data:
            return CompanyData(
                siret=siret,
                erreur="SIRET non trouve dans INSEE et RNE",
            )

        # Process INSEE data
        if insee_data:
            insee_extracted = self.insee_client.extract_data(insee_data)

            result["raison_sociale"] = insee_extracted.get("raison_sociale", "")
            result["adresse"] = insee_extracted.get("adresse", "")
            result["code_postal"] = insee_extracted.get("code_postal", "")
            result["ville"] = insee_extracted.get("ville", "")
            result["code_ape"] = insee_extracted.get("code_ape", "")

            # Calculate derived fields
            categorie = insee_extracted.get("categorie_juridique", "")
            result["forme_juridique"] = get_forme_juridique(categorie)
            result["tva_intracommunautaire"] = calc_tva_intracommunautaire(siren)
            result["rcs"] = format_rcs(siren, result["ville"])
        else:
            donnees_partielles = True
            erreur = "Donnees INSEE non disponibles"

        # Process RNE data
        if rne_data:
            rne_extracted = self.rne_client.extract_all(rne_data)

            result["capital"] = rne_extracted.get("capital", "")
            result["civilite_contact"] = rne_extracted.get("civilite_contact", "")
            result["nom_contact"] = rne_extracted.get("nom_contact", "")
            result["prenom_contact"] = rne_extracted.get("prenom_contact", "")
            result["fonction_contact"] = rne_extracted.get("fonction_contact", "")
        else:
            if not donnees_partielles:
                donnees_partielles = True
                erreur = "Donnees RNE non disponibles (capital et dirigeants)"

        return CompanyData(
            **result,
            donnees_partielles=donnees_partielles,
            erreur=erreur,
        )

    async def process_batch(
        self,
        sirets: list[str],
        progress_callback=None,
    ) -> list[CompanyData]:
        """Process a batch of SIRET numbers.

        Args:
            sirets: List of SIRET numbers
            progress_callback: Optional callback for progress updates

        Returns:
            List of CompanyData objects
        """
        results = []
        total = len(sirets)

        for i, siret in enumerate(sirets):
            try:
                result = await self.process_siret(siret)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {siret}: {e}")
                results.append(CompanyData(siret=siret, erreur=str(e)))

            if progress_callback:
                await progress_callback(i + 1, total)

        return results

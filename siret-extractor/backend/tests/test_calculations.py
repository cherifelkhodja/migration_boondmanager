"""Tests for critical calculations in the SIRET extractor."""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_processor import (
    calc_tva_intracommunautaire,
    format_rcs,
    format_capital,
    get_forme_juridique,
    validate_siret,
)


class TestTVACalculation:
    """Tests for TVA intracommunautaire calculation."""

    def test_calc_tva_a2net(self):
        """Test TVA calculation for A2NET Consulting."""
        assert calc_tva_intracommunautaire("943460824") == "FR84943460824"

    def test_calc_tva_hightekers(self):
        """Test TVA calculation for Hightekers."""
        assert calc_tva_intracommunautaire("851267245") == "FR06851267245"

    def test_calc_tva_human_portage(self):
        """Test TVA calculation for Human Portage."""
        assert calc_tva_intracommunautaire("878918697") == "FR30878918697"

    def test_calc_tva_little_big(self):
        """Test TVA calculation for Little Big Connection."""
        assert calc_tva_intracommunautaire("793569757") == "FR78793569757"

    def test_calc_tva_optim_portage(self):
        """Test TVA calculation for OPTIM Portage."""
        assert calc_tva_intracommunautaire("837601327") == "FR34837601327"

    def test_calc_tva_invalid_siren(self):
        """Test TVA calculation with invalid SIREN."""
        assert calc_tva_intracommunautaire("") == ""
        assert calc_tva_intracommunautaire("abc") == ""


class TestRCSFormat:
    """Tests for RCS formatting."""

    def test_format_rcs_paris(self):
        """Test RCS format for Paris."""
        assert format_rcs("943460824", "Paris") == "943 460 824 R.C.S. Paris"

    def test_format_rcs_lyon(self):
        """Test RCS format for Lyon."""
        assert format_rcs("851267245", "Lyon") == "851 267 245 R.C.S. Lyon"

    def test_format_rcs_no_city(self):
        """Test RCS format without city."""
        assert format_rcs("943460824", "") == "943 460 824"

    def test_format_rcs_invalid_siren(self):
        """Test RCS format with invalid SIREN."""
        assert format_rcs("", "Paris") == ""
        assert format_rcs("12345", "Paris") == ""


class TestCapitalFormat:
    """Tests for capital formatting."""

    def test_format_capital_50000(self):
        """Test capital format for 50000."""
        result = format_capital(50000)
        assert "50" in result
        assert "000" in result
        assert "00" in result

    def test_format_capital_100100(self):
        """Test capital format for 100100."""
        result = format_capital(100100)
        assert "100" in result

    def test_format_capital_zero(self):
        """Test capital format for zero."""
        assert format_capital(0) == ""

    def test_format_capital_none(self):
        """Test capital format for None."""
        assert format_capital(None) == ""


class TestFormeJuridique:
    """Tests for legal form mapping."""

    def test_forme_ei(self):
        """Test EI detection."""
        assert get_forme_juridique("1000") == "EI"

    def test_forme_eurl(self):
        """Test EURL detection."""
        assert get_forme_juridique("5498") == "EURL"

    def test_forme_sarl(self):
        """Test SARL detection."""
        assert get_forme_juridique("5499") == "SARL"

    def test_forme_sas(self):
        """Test SAS detection."""
        assert get_forme_juridique("5710") == "SAS"

    def test_forme_sasu(self):
        """Test SASU detection."""
        assert get_forme_juridique("5720") == "SASU"

    def test_forme_unknown(self):
        """Test unknown category returns the code."""
        result = get_forme_juridique("9999")
        assert result in ("9999", "")

    def test_forme_empty(self):
        """Test empty category."""
        assert get_forme_juridique("") == ""


class TestSiretValidation:
    """Tests for SIRET validation."""

    def test_valid_siret_14_digits(self):
        """Test valid 14-digit SIRET."""
        is_valid, error = validate_siret("94346082400015")
        assert is_valid is True
        assert error == ""

    def test_invalid_siret_too_short(self):
        """Test SIRET with too few digits."""
        is_valid, error = validate_siret("943460824")
        assert is_valid is False
        assert "14" in error

    def test_invalid_siret_too_long(self):
        """Test SIRET with too many digits."""
        is_valid, error = validate_siret("943460824000150")
        assert is_valid is False
        assert "14" in error

    def test_invalid_siret_empty(self):
        """Test empty SIRET."""
        is_valid, error = validate_siret("")
        assert is_valid is False
        assert "vide" in error.lower()

    def test_siret_with_spaces(self):
        """Test SIRET with spaces is cleaned."""
        is_valid, error = validate_siret("943 460 824 00015")
        assert is_valid is True

    def test_siret_with_dashes(self):
        """Test SIRET with dashes is cleaned."""
        is_valid, error = validate_siret("943-460-824-00015")
        assert is_valid is True


class TestRNEClientExtraction:
    """Tests for RNE client data extraction."""

    def test_extract_capital_from_valid_data(self):
        """Test capital extraction from valid RNE response."""
        from services.rne_client import RNEClient

        client = RNEClient()

        data = {
            "formality": {
                "content": {
                    "personneMorale": {
                        "identite": {
                            "description": {
                                "capitalSocial": {
                                    "montant": 50000,
                                    "devise": "EUR"
                                }
                            }
                        }
                    }
                }
            }
        }

        result = client.extract_capital(data)
        assert "50" in result
        assert "000" in result

    def test_extract_capital_missing_data(self):
        """Test capital extraction from missing data."""
        from services.rne_client import RNEClient

        client = RNEClient()
        result = client.extract_capital({})
        assert result == ""

    def test_extract_dirigeant_president(self):
        """Test dirigeant extraction prioritizes President."""
        from services.rne_client import RNEClient

        client = RNEClient()

        data = {
            "formality": {
                "content": {
                    "personneMorale": {
                        "composition": {
                            "pouvoirs": [
                                {
                                    "typeDePersonne": "PERSONNE_PHYSIQUE",
                                    "roleEntreprise": "DIRECTEUR_GENERAL",
                                    "individu": {
                                        "descriptionPersonne": {
                                            "nom": "MARTIN",
                                            "prenoms": "Pierre",
                                        }
                                    }
                                },
                                {
                                    "typeDePersonne": "PERSONNE_PHYSIQUE",
                                    "roleEntreprise": "PRESIDENT",
                                    "individu": {
                                        "descriptionPersonne": {
                                            "nom": "DUPONT",
                                            "prenoms": "Jean",
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }

        result = client.extract_dirigeant_principal(data)
        assert result["nom"] == "DUPONT"
        assert result["prenom"] == "Jean"
        assert result["fonction"] == "President"

    def test_extract_dirigeant_fallback_first(self):
        """Test dirigeant extraction falls back to first person."""
        from services.rne_client import RNEClient

        client = RNEClient()

        data = {
            "formality": {
                "content": {
                    "personneMorale": {
                        "composition": {
                            "pouvoirs": [
                                {
                                    "typeDePersonne": "PERSONNE_PHYSIQUE",
                                    "roleEntreprise": "MEMBRE",
                                    "individu": {
                                        "descriptionPersonne": {
                                            "nom": "DURAND",
                                            "prenoms": "Marie",
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }

        result = client.extract_dirigeant_principal(data)
        assert result["nom"] == "DURAND"
        assert result["prenom"] == "Marie"

    def test_map_role(self):
        """Test role mapping."""
        from services.rne_client import RNEClient

        client = RNEClient()

        assert client._map_role("PRESIDENT") == "President"
        assert client._map_role("GERANT") == "Gerant"
        assert client._map_role("DIRECTEUR_GENERAL") == "Directeur General"
        assert client._map_role("UNKNOWN_ROLE") == "Unknown Role"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

from app.detectors.grounding import GroundingDetector


def test_supported_claim():
    _, claims = GroundingDetector().detect("Project Atlas launched in June 2024.")
    assert claims[0].status == "SUPPORTED"


def test_contradicted_date():
    _, claims = GroundingDetector().detect("Project Atlas launched in March 2024.")
    assert claims[0].status == "CONTRADICTED"
    assert "conflicting date" in claims[0].explanation


def test_unsupported_numeric_claim():
    _, claims = GroundingDetector().detect("Project Atlas generated $23 million in its first quarter.")
    assert claims[0].status == "UNSUPPORTED"
    assert "No supporting evidence" in claims[0].explanation


def test_insufficient_evidence_is_not_called_false():
    claim = GroundingDetector().assess_claim("Quasar ZX is translucent")
    assert claim.status == "INSUFFICIENT_EVIDENCE"
    assert "insufficient" in claim.explanation.lower()


def test_compound_claims_are_split_and_distinguished():
    signal, claims = GroundingDetector().detect("Project Atlas launched in March 2024 and generated $23 million in its first quarter.")
    assert [claim.status for claim in claims] == ["CONTRADICTED", "UNSUPPORTED"]
    assert signal.score == 0.72

from app.detectors.privacy import PrivacyDetector


def test_detects_email_and_redacts_readably():
    detector = PrivacyDetector()
    text = "Contact the fictional user at demo.user@example.test for help."
    signal = detector.detect(text)
    assert signal.score >= 0.6
    assert signal.signals[0]["entity_type"] == "EMAIL"
    assert detector.redact(text) == "Contact the fictional user at [EMAIL] for help."


def test_detects_phone():
    signal = PrivacyDetector().detect("Call +91 98765 43210 for the synthetic case.")
    assert any(item["entity_type"] == "PHONE" for item in signal.signals)


def test_detects_secret_without_returning_value():
    secret = "sk-demoSecretTokenABCDE12345"
    signal = PrivacyDetector().detect(f"Credential: {secret}")
    assert signal.score == 0.99
    assert secret not in str(signal.model_dump())


def test_validates_luhn_card():
    detector = PrivacyDetector()
    good = detector.detect("Synthetic card: 4111 1111 1111 1111")
    bad = detector.detect("Invoice reference: 0000 0000 0000 0000")
    assert any(item["entity_type"] == "CREDIT_CARD" for item in good.signals)
    assert not any(item["entity_type"] == "CREDIT_CARD" for item in bad.signals)


def test_avoids_obvious_number_false_positive():
    assert PrivacyDetector().detect("Release version 2024.06.15 is public.").score == 0

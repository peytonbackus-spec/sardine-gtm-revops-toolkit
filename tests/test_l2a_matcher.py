import pytest

from gtm_engineer.enrichment.l2a_matcher import (
    AccountRecord,
    LeadRecord,
    LeadToAccountMatcher,
    jaro_winkler_similarity,
    normalize_company_name,
    normalize_domain,
)


class TestNormalizations:
    def test_normalize_domain_subdomains_and_protocols(self):
        assert normalize_domain("https://www.acme.corp.com/login") == "acme.corp.com"
        assert normalize_domain("app.hubspot.com") == "hubspot.com"
        assert normalize_domain("pat@blog.stripe.com") == "stripe.com"

    def test_normalize_domain_suppresses_free_providers(self):
        assert normalize_domain("pat@gmail.com") is None
        assert normalize_domain("user@yahoo.com") is None
        assert normalize_domain("contact@protonmail.com") is None

    def test_normalize_company_name_strips_legal_suffixes(self):
        assert normalize_company_name("Acme Technologies, Inc.") == "acme"
        assert normalize_company_name("Stripe Group LLC") == "stripe"
        assert normalize_company_name("Snowflake Global Ltd.") == "snowflake"

    def test_normalize_company_name_handles_no_suffix(self):
        assert normalize_company_name("OpenAI") == "openai"

class TestJaroWinklerSimilarity:
    def test_exact_matches(self):
        assert jaro_winkler_similarity("datacamp", "datacamp") == 1.0

    def test_similar_names(self):
        score = jaro_winkler_similarity("mcdonalds", "macdonalds")
        assert score >= 0.88

    def test_completely_different_names(self):
        score = jaro_winkler_similarity("apple", "microsoft")
        assert score < 0.50

class TestLeadToAccountMatcherCascades:
    @pytest.fixture
    def sample_accounts(self):
        return [
            AccountRecord(
                id="acc_1",
                name="Acme Corporation",
                primary_domain="acme.com",
                secondary_domains=["acme.co.uk"],
            ),
            AccountRecord(
                id="acc_2",
                name="Stripe Technologies Inc",
                primary_domain="stripe.com",
            ),
        ]

    def test_tier_1_exact_domain_match(self, sample_accounts):
        matcher = LeadToAccountMatcher()
        lead = LeadRecord(id="l1", email="pat@acme.co.uk", company_name="Unknown")
        result = matcher.find_match(lead, sample_accounts)

        assert result.account_id == "acc_1"
        assert result.confidence_score == 1.0
        assert result.match_strategy == "exact_domain"

    def test_tier_2_exact_normalized_name_match(self, sample_accounts):
        matcher = LeadToAccountMatcher()
        lead = LeadRecord(id="l2", email="pat@gmail.com", company_name="Stripe Ltd")
        result = matcher.find_match(lead, sample_accounts)

        assert result.account_id == "acc_2"
        assert result.confidence_score == 0.98
        assert result.match_strategy == "exact_normalized_name"

    def test_tier_3_fuzzy_jaro_winkler_match(self, sample_accounts):
        matcher = LeadToAccountMatcher()
        lead = LeadRecord(id="l3", email="user@gmail.com", company_name="Strype Tech")
        result = matcher.find_match(lead, sample_accounts)

        assert result.account_id == "acc_2"
        assert result.confidence_score >= 0.88
        assert result.match_strategy == "fuzzy_jaro_winkler"

    def test_tier_4_unmatched_fallback(self, sample_accounts):
        matcher = LeadToAccountMatcher()
        lead = LeadRecord(id="l4", email="user@gmail.com", company_name="Random Startup")
        result = matcher.find_match(lead, sample_accounts)

        assert result.account_id is None
        assert result.confidence_score == 0.0
        assert result.match_strategy == "unmatched"

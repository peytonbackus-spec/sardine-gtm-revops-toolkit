import pytest

from gtm_engineer.enrichment.rules_engine import AttributeDict, WaterfallEnrichmentEngine


class TestAttributeDict:
    def test_dot_notation_access(self):
        data = AttributeDict({"contact": {"email": "test@stripe.com", "title": "VP RevOps"}})
        assert data.contact.email == "test@stripe.com"
        assert data.contact.title == "VP RevOps"

    def test_missing_attribute_returns_none(self):
        data = AttributeDict({"contact": {"email": "test@stripe.com"}})
        assert data.contact.non_existent is None
        assert data.missing_key is None

class TestWaterfallEnrichmentEngine:
    @pytest.fixture
    def engine(self):
        return WaterfallEnrichmentEngine("config/waterfall_rules.yaml")

    def test_evaluate_condition_valid_expression(self, engine):
        state = {"zerobounce": {"status": "catch_all"}}
        condition = "zerobounce.status in ['catch_all', 'unknown']"
        assert engine._evaluate_condition(condition, state) is True

    def test_evaluate_condition_failing_expression(self, engine):
        state = {"zerobounce": {"status": "valid"}}
        condition = "zerobounce.status in ['catch_all', 'unknown']"
        assert engine._evaluate_condition(condition, state) is False

    def test_check_success_criteria(self, engine):
        step_result = {"status": "valid", "score": 98}
        success_criteria = "status == 'valid'"
        assert engine._check_success(success_criteria, step_result) is True

    @pytest.mark.asyncio
    async def test_execute_email_validation_stage(self, engine):
        input_data = {"email": "pat@acme.com"}
        result = await engine.execute_waterfall_stage("email_validation", input_data)

        assert result["zerobounce"]["status"] == "valid"
        assert result["status"] == "valid"
        assert "neverbounce" not in result

    @pytest.mark.asyncio
    async def test_execute_full_pipeline_success(self, engine):
        input_data = {"email": "pat@stripe.com", "domain": "stripe.com"}
        result = await engine.execute_full_pipeline(input_data)

        assert result["zerobounce"]["status"] == "valid"
        assert result["clay"]["contact"]["title"] == "VP of Revenue Operations"
        assert result["clearbit"]["account"]["employee_count"] == 250

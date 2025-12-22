import asyncio
import unittest
from unittest.mock import MagicMock, patch
from app.services.ai_classifier_service import AIScopeClassifierService

class TestGroqClassifier(unittest.TestCase):
    def setUp(self):
        # We need to patch the settings BEFORE initializing the service OR patch the client inside
        with patch("app.config.settings.GROQ_API_KEY", "test_key"):
            self.service = AIScopeClassifierService()
            self.service.client = MagicMock()

    @patch("app.config.settings.GROQ_API_KEY", "test_key")
    def test_prompt_builder(self):
        rows = [{"description": "Flight to Paris", "category": "Travel"}]
        prompt = self.service._build_scope_prompt(rows)
        self.assertIn("Business Travel", prompt)
        self.assertIn("Flight to Paris", prompt)
        self.assertIn("Decision Trees", prompt)

    @patch("app.config.settings.GROQ_API_KEY", "test_key")
    def test_parse_response(self):
        content = """
        {
            "classifications": [
                {
                    "index": 0,
                    "scope": "Scope 3",
                    "scope3Category": "6 - Business Travel",
                    "reasoning": "Air travel for meeting",
                    "confidence": 0.99
                }
            ]
        }
        """
        results = self.service._parse_groq_response(content)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["scope"], "Scope 3")
        self.assertEqual(results[0]["scope3Category"], "6 - Business Travel")

    @patch("app.config.settings.GROQ_API_KEY", "test_key")
    async def test_classify_batch_mocked(self):
        # Mocking the synchronous client call in an async wrapper
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content='{"classifications": [{"index": 0, "scope": "Scope 3", "scope3Category": "6 - Business Travel", "reasoning": "test", "confidence": 0.9}]}'))]
        self.service.client.chat.completions.create.return_value = mock_completion
        
        rows = [{"description": "Flight to Paris", "category": "Travel"}]
        results = await self.service.classify_batch(rows)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["scope"], "Scope 3")
        self.assertEqual(results[0]["scope3Category"], "6 - Business Travel")
        self.assertFalse(results[0]["needs_review"])

    def test_fallback_logic(self):
        rows = [{"description": "Electricity bill", "category": "Utilities"}]
        results = self.service._fallback_classify(rows, "API Error")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["scope"], "Scope 2")
        self.assertIn("API Error", results[0]["reasoning"])

async def run_tests():
    # Helper to run async tests in unittest
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGroqClassifier)
    # This is a bit hacky for a script, but standard unittest.main() doesn't like async
    for test_name in suite.getTestCaseNames():
        test = TestGroqClassifier(test_name)
        if hasattr(test, test_name) and asyncio.iscoroutinefunction(getattr(test, test_name)):
            # Handle async test
            await test.setUp()
            await getattr(test, test_name)()
        else:
            # Handle sync test
            test.setUp()
            getattr(test, test_name)()
    print("\nAll mocked tests passed!")

if __name__ == "__main__":
    asyncio.run(run_tests())

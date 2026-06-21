from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, MagicMock, patch

from langgraph_course.utils.llm import LLMFactory, get_llm, get_openrouter_llm


class FakeProvider:
    name = "fake"

    def create_llm(self, model=None, temperature=None):
        return MagicMock()

    async def call(self, prompt: str) -> str:
        return "fake response"

    def validate_config(self):
        pass


@patch("langgraph_course.utils.llm.get_provider", return_value=FakeProvider)
@patch("langgraph_course.utils.llm.settings")
class TestLLMFactory(TestCase):
    def setUp(self) -> None:
        LLMFactory._cache.clear()

    def tearDown(self) -> None:
        LLMFactory._cache.clear()

    def test_create_uses_named_provider(
        self, mock_settings: MagicMock, mock_get_provider: MagicMock
    ) -> None:
        mock_settings.llm_provider = "auto"
        result = LLMFactory.create(provider="fake")
        self.assertIsNotNone(result)
        mock_get_provider.assert_called_with("fake")

    def test_create_falls_back_to_settings_provider(
        self, mock_settings: MagicMock, mock_get_provider: MagicMock
    ) -> None:
        mock_settings.llm_provider = "fake"
        result = LLMFactory.create()
        self.assertIsNotNone(result)
        mock_get_provider.assert_called_with("fake")

    def test_cached_returns_same_instance(
        self, mock_settings: MagicMock, mock_get_provider: MagicMock
    ) -> None:
        mock_settings.llm_provider = "fake"
        mock_settings.llm_model = "gpt-4o"
        first = LLMFactory.cached(provider="fake")
        second = LLMFactory.cached(provider="fake")
        self.assertIs(first, second)

    def test_cached_different_keys_different_instances(
        self, mock_settings: MagicMock, mock_get_provider: MagicMock
    ) -> None:
        mock_settings.llm_provider = "fake"
        mock_settings.llm_model = "gpt-4o"
        a = LLMFactory.cached(provider="fake", model="gpt-4o")
        b = LLMFactory.cached(provider="fake", model="claude-3")
        self.assertIsNot(a, b)


@patch("langgraph_course.utils.llm.settings")
class TestLLMFactoryAliases(TestCase):
    def test_default_delegates_to_create(
        self, mock_settings: MagicMock
    ) -> None:
        with patch.object(LLMFactory, "create") as mock_create:
            LLMFactory.default(model="m", temperature=0.5)
            mock_create.assert_called_once_with(model="m", temperature=0.5)

    def test_openrouter_delegates_to_create_with_openrouter(
        self, mock_settings: MagicMock
    ) -> None:
        with patch.object(LLMFactory, "create") as mock_create:
            LLMFactory.openrouter(model="m", temperature=0.5)
            mock_create.assert_called_once_with(
                provider="openrouter", model="m", temperature=0.5
            )


class TestLLMModuleLevelAliases(TestCase):
    def test_module_level_aliases_exist(self) -> None:
        self.assertIs(get_llm, LLMFactory.default)
        self.assertIs(get_openrouter_llm, LLMFactory.openrouter)

    def test_registry_contains_builtin_providers(self) -> None:
        from langgraph_course.utils.providers.base import _PROVIDERS
        self.assertIn("auto", _PROVIDERS)
        self.assertIn("openrouter", _PROVIDERS)
        self.assertIn("openai", _PROVIDERS)
        self.assertIn("anthropic", _PROVIDERS)


class TestLLMProviderValidation(TestCase):
    @patch("langgraph_course.utils.llm.get_provider")
    @patch("langgraph_course.utils.llm.settings")
    def test_create_raises_for_unknown_provider(
        self, mock_settings: MagicMock, mock_get_provider: MagicMock
    ) -> None:
        mock_get_provider.side_effect = ValueError("Unknown provider")
        mock_settings.llm_provider = "nope"
        with self.assertRaises(ValueError):
            LLMFactory.create(provider="nope")


@patch("langgraph_course.utils.llm.get_provider", return_value=FakeProvider)
@patch("langgraph_course.utils.llm.settings")
class TestLLMFactoryAsyncCall(IsolatedAsyncioTestCase):
    async def test_call_returns_string(
        self, mock_settings: MagicMock, mock_get_provider: MagicMock
    ) -> None:
        mock_settings.llm_provider = "fake"
        result = await LLMFactory.call("hello")
        self.assertEqual(result, "fake response")

    async def test_call_passes_prompt(
        self, mock_settings: MagicMock, mock_get_provider: MagicMock
    ) -> None:
        mock_settings.llm_provider = "fake"
        with patch.object(FakeProvider, "call", new_callable=AsyncMock) as mock_fake_call:
            mock_fake_call.return_value = "yes"
            result = await LLMFactory.call("what?")
            mock_fake_call.assert_called_once_with("what?")
            self.assertEqual(result, "yes")

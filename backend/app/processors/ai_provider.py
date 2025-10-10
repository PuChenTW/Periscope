"""
AI provider abstraction for similarity detection.

This module provides an abstraction layer for AI model providers, making it easy
to switch between different AI services (Gemini, OpenAI, Anthropic, etc.) without
modifying the core similarity detection logic.
"""

from typing import Protocol

from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider as PydanticOpenAIProvider

from app.config import Settings


class AIProvider(Protocol):
    """Protocol for AI model providers."""

    def create_agent(self, output_type: type, system_prompt: str) -> Agent:
        """
        Create a PydanticAI agent with the specified configuration.

        Args:
            output_type: The Pydantic model type for agent output
            system_prompt: The system prompt for the agent

        Returns:
            Configured PydanticAI Agent instance
        """
        ...


class GeminiProvider:
    """Google Gemini AI provider implementation."""

    def __init__(self, settings: Settings):
        """
        Initialize Gemini provider.

        Args:
            settings: Application settings containing Gemini configuration
        """
        provider = GoogleProvider(api_key=settings.ai.gemini_api_key)
        self.model = GoogleModel(settings.ai.gemini_model, provider=provider)

    def create_agent(self, output_type: type, system_prompt: str) -> Agent:
        """
        Create a PydanticAI agent configured for Gemini.

        Args:
            output_type: The Pydantic model type for agent output
            system_prompt: The system prompt for the agent

        Returns:
            Configured PydanticAI Agent instance using Gemini
        """
        return Agent(
            self.model,
            output_type=output_type,
            system_prompt=system_prompt,
        )


class OpenAIProvider:
    """OpenAI provider implementation."""

    def __init__(self, settings: Settings):
        """
        Initialize OpenAI provider.

        Args:
            settings: Application settings containing OpenAI configuration
        """
        provider = PydanticOpenAIProvider(api_key=settings.ai.openai_api_key)
        model = OpenAIChatModel(settings.ai.openai_model, provider=provider)
        self.model = model

    def create_agent(self, output_type: type, system_prompt: str) -> Agent:
        """
        Create a PydanticAI agent configured for OpenAI.

        Args:
            output_type: The Pydantic model type for agent output
            system_prompt: The system prompt for the agent

        Returns:
            Configured PydanticAI Agent instance using OpenAI
        """
        return Agent(
            self.model,
            output_type=output_type,
            system_prompt=system_prompt,
        )


def create_ai_provider(settings: Settings) -> AIProvider:
    """
    Factory function to create an AI provider based on settings.

    Args:
        settings: Application settings containing AI provider configuration

    Returns:
        Configured AI provider instance

    Raises:
        ValueError: If the configured AI provider is not supported
    """
    provider = settings.ai.provider.lower()

    if provider == "gemini":
        return GeminiProvider(settings)
    elif provider == "openai":
        return OpenAIProvider(settings)
    else:
        raise ValueError(f"Unsupported AI provider: {provider}. Supported providers: gemini, openai")

"""System prompts and templates for the AI chatbot."""

from typing import Dict, Any


def get_system_prompt(prompt_type: str = "default") -> str:
    """
    Get the system prompt for the chatbot.

    Args:
        prompt_type: Type of prompt (default, creative, concise)

    Returns:
        System prompt string
    """
    prompts = {
        "default": _get_default_prompt(),
        "creative": _get_creative_prompt(),
        "concise": _get_concise_prompt()
    }

    return prompts.get(prompt_type, prompts["default"])


def _get_default_prompt() -> str:
    """Get the default system prompt."""
    return """You are a helpful AI assistant powered by Claude and running on AWS. You are designed to be friendly, informative, and respectful.

Your capabilities include:
- Answering questions on a wide range of topics
- Providing explanations and insights
- Helping with creative tasks
- Assisting with problem-solving
- Offering suggestions and recommendations

Guidelines:
- Be clear and concise in your responses
- If you're unsure about something, acknowledge it
- Respect user privacy and don't ask for personal information
- Avoid harmful, unethical, or inappropriate content
- Provide accurate information to the best of your ability

You are running in a serverless environment on AWS Lambda, using API Gateway and Bedrock. You're part of a learning project for cloud infrastructure and AI applications."""


def _get_creative_prompt() -> str:
    """Get a more creative system prompt."""
    return """You are an imaginative and creative AI assistant. You love to explore ideas, think outside the box, and help users with creative endeavors.

Your strengths include:
- Creative writing and storytelling
- Brainstorming innovative ideas
- Exploring different perspectives
- Making connections between seemingly unrelated concepts
- Providing artistic and creative suggestions

Be playful, imaginative, and don't be afraid to take creative risks while still being helpful and respectful."""


def _get_concise_prompt() -> str:
    """Get a concise, direct system prompt."""
    return """You are a direct and efficient AI assistant. Provide clear, accurate, and concise responses.

Focus on:
- Getting straight to the point
- Being accurate and factual
- Avoiding unnecessary elaboration
- Providing the most relevant information first

Keep responses brief unless the user asks for more detail."""


def format_conversation_history(history: list) -> list:
    """
    Format conversation history for the API.

    Args:
        history: List of conversation turns

    Returns:
        Formatted history list
    """
    formatted = []

    for turn in history:
        role = turn.get("role", "user")
        content = turn.get("content", "")

        if role in ["user", "assistant"]:
            formatted.append({
                "role": role,
                "content": content
            })

    return formatted


def build_prompt_with_context(user_message: str, context: Dict[str, Any]) -> str:
    """
    Build a prompt with additional context.

    Args:
        user_message: The user's message
        context: Additional context (e.g., user preferences, session info)

    Returns:
        Enhanced prompt string
    """
    enhanced_prompt = user_message

    # Add context if available
    if context.get("user_name"):
        enhanced_prompt = f"[User: {context['user_name']}]\n\n{user_message}"

    if context.get("session_context"):
        enhanced_prompt = f"[Session Context: {context['session_context']}]\n\n{enhanced_prompt}"

    return enhanced_prompt

"""
IRIS AI — LLM Service
Handles multi-turn conversations, intent classification, model fallback,
and streaming responses via LiteLLM → OpenRouter.
"""
import json
import re
from typing import AsyncGenerator, List, Optional
import litellm
from litellm import completion, acompletion
from app.core.config import settings

# Configure LiteLLM
litellm.set_verbose = False
litellm.drop_params = True   # Drop unsupported params silently


IRIS_SYSTEM_PROMPT = """You are IRIS (Intelligent Responsive Integrated System), 
a highly advanced personal AI assistant inspired by J.A.R.V.I.S. from Iron Man.

Your personality:
- Highly intelligent, precise, and efficient
- Slightly formal but personable — like a professional assistant
- Proactive: anticipate needs and offer suggestions
- Concise: don't over-explain unless asked

Your capabilities:
- Answer questions and have natural conversations
- Control devices (PC, Mac, Android) via special action tags
- Manage tasks, notes, reminders, and calendar
- Read and compose emails
- Analyze documents and summarize content
- Monitor system health across all connected devices

When you need to perform a device action, include it in your response using this exact format:
[ACTION:action_name:{"param1": "value1"}]

Available actions:
- [ACTION:lock_screen:{}]
- [ACTION:open_browser:{"url": "https://example.com"}]
- [ACTION:open_app:{"name": "Chrome"}]
- [ACTION:set_volume:{"level": 50}]
- [ACTION:set_brightness:{"level": 80}]
- [ACTION:sleep:{}]
- [ACTION:shutdown:{}]
- [ACTION:take_screenshot:{}]
- [ACTION:search_files:{"query": "filename"}]
- [ACTION:type_text:{"text": "Hello world"}]
- [ACTION:send_whatsapp:{"contact": "John", "message": "Hello!"}]
- [ACTION:send_sms:{"number": "+1234567890", "message": "Hello!"}]
- [ACTION:make_call:{"number": "+1234567890"}]

Always respond naturally first, then add the action tag if needed.
Example: "Of course! I'll lock your screen now. [ACTION:lock_screen:{}]"

Current context:
"""


class LLMService:
    def __init__(self):
        self.primary_model = settings.PRIMARY_MODEL
        self.fallback_models = settings.FALLBACK_MODELS
        self._configure_openrouter()

    def _configure_openrouter(self):
        """Configure LiteLLM for OpenRouter."""
        if settings.OPENROUTER_API_KEY:
            litellm.api_key = settings.OPENROUTER_API_KEY
            litellm.api_base = settings.OPENROUTER_BASE_URL

    def _build_messages(
        self,
        user_message: str,
        conversation_history: Optional[List[dict]] = None,
        memory_context: str = "",
        user_info: str = "",
    ) -> List[dict]:
        """Build message array for LLM including history and memory context."""
        system_content = IRIS_SYSTEM_PROMPT
        if memory_context:
            system_content += f"\nRelevant memory context:\n{memory_context}"
        if user_info:
            system_content += f"\nUser info: {user_info}"

        messages = [{"role": "system", "content": system_content}]

        # Add conversation history (limited to avoid context window overflow)
        if conversation_history:
            history = conversation_history[-settings.MAX_CONVERSATION_HISTORY:]
            for msg in history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        messages.append({"role": "user", "content": user_message})
        return messages

    def generate_response(
        self,
        user_message: str,
        conversation_history: Optional[List[dict]] = None,
        memory_context: str = "",
        user_info: str = "",
    ) -> dict:
        """
        Synchronous generation with automatic model fallback.
        Returns: {content, model_used, tokens_used, intent, command}
        """
        messages = self._build_messages(
            user_message, conversation_history, memory_context, user_info
        )

        models_to_try = [self.primary_model] + self.fallback_models
        last_error = None

        for model in models_to_try:
            try:
                response = completion(
                    model=model,
                    messages=messages,
                    max_tokens=1024,
                    temperature=0.7,
                    timeout=30,
                    extra_headers={
                        "HTTP-Referer": "https://iris-ai.local",
                        "X-Title": "IRIS AI",
                    },
                )
                content = response.choices[0].message.content
                tokens = response.usage.total_tokens if response.usage else None

                intent, command = self._parse_intent(content)
                clean_content = self._clean_action_tags(content)

                return {
                    "content": clean_content,
                    "raw_content": content,
                    "model_used": model,
                    "tokens_used": tokens,
                    "intent": intent,
                    "command": command,
                }
            except Exception as e:
                last_error = e
                continue

        # All models failed
        return {
            "content": f"I'm having trouble connecting to my AI systems right now. Please check your OpenRouter API key and try again.",
            "raw_content": "",
            "model_used": None,
            "tokens_used": None,
            "intent": "error",
            "command": None,
            "error": str(last_error),
        }

    async def generate_response_stream(
        self,
        user_message: str,
        conversation_history: Optional[List[dict]] = None,
        memory_context: str = "",
        user_info: str = "",
    ) -> AsyncGenerator[str, None]:
        """
        Async streaming generator. Yields JSON chunks.
        Each chunk: {"type": "delta", "content": "..."}
        Final chunk: {"type": "done", "intent": "...", "command": {...}}
        """
        messages = self._build_messages(
            user_message, conversation_history, memory_context, user_info
        )

        models_to_try = [self.primary_model] + self.fallback_models
        full_content = ""

        for model in models_to_try:
            try:
                response = await acompletion(
                    model=model,
                    messages=messages,
                    max_tokens=1024,
                    temperature=0.7,
                    stream=True,
                    extra_headers={
                        "HTTP-Referer": "https://iris-ai.local",
                        "X-Title": "IRIS AI",
                    },
                )

                async for chunk in response:
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        full_content += delta
                        clean = self._clean_action_tags(delta)
                        if clean:
                            yield json.dumps({"type": "delta", "content": clean})

                intent, command = self._parse_intent(full_content)
                yield json.dumps({
                    "type": "done",
                    "intent": intent,
                    "command": command,
                    "model": model,
                })
                return

            except Exception:
                continue

        yield json.dumps({
            "type": "error",
            "content": "Connection to AI systems failed. Check your API key.",
        })

    def _parse_intent(self, content: str) -> tuple[Optional[str], Optional[dict]]:
        """
        Parse [ACTION:action_name:{params}] tags from LLM response.
        Returns (intent_name, command_dict) or (None, None).
        """
        pattern = r'\[ACTION:([a-z_]+):(\{[^}]*\})\]'
        match = re.search(pattern, content)
        if match:
            action_name = match.group(1)
            try:
                params = json.loads(match.group(2))
            except json.JSONDecodeError:
                params = {}
            return action_name, {"action": action_name, "params": params}
        return None, None

    def _clean_action_tags(self, content: str) -> str:
        """Remove [ACTION:...] tags from content for display."""
        return re.sub(r'\[ACTION:[^\]]+\]', '', content).strip()

    def classify_intent_simple(self, message: str) -> str:
        """
        Fast rule-based intent classification (no LLM call needed).
        Returns intent category string.
        """
        msg = message.lower()
        if any(w in msg for w in ["lock", "sleep", "shutdown", "restart", "hibernate"]):
            return "device_control"
        if any(w in msg for w in ["volume", "brightness", "mute"]):
            return "system_settings"
        if any(w in msg for w in ["open", "launch", "start", "close", "quit"]):
            return "app_control"
        if any(w in msg for w in ["email", "mail", "inbox", "compose", "send email"]):
            return "email"
        if any(w in msg for w in ["task", "todo", "reminder", "note"]):
            return "productivity"
        if any(w in msg for w in ["whatsapp", "sms", "message", "call", "text"]):
            return "communication"
        if any(w in msg for w in ["weather", "news", "search", "find", "look up"]):
            return "information"
        return "conversation"


llm_service = LLMService()

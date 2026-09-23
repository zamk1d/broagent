import json
import time

from .. import config


class ModelClient:
    def __init__(self):
        self.provider = config.PROVIDER
        if self.provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        elif self.provider == "groq":
            from openai import OpenAI
            self._client = OpenAI(base_url=config.GROQ_BASE_URL, api_key=config.GROQ_API_KEY)
        else:
            raise ValueError(
                f"Неизвестный BROAGENT_PROVIDER={self.provider!r}, ожидается 'anthropic' или 'groq'"
            )

    def ask(self, system: str, messages: list, tools: list, max_retries: int = 3) -> dict:
        if self.provider == "anthropic":
            return self._ask_anthropic(system, messages, tools, max_retries)
        return self._ask_groq(system, messages, tools, max_retries)

    def _ask_anthropic(self, system, messages, tools, max_retries):
        import anthropic
        last_err = None
        kwargs = dict(model=config.ANTHROPIC_MODEL, max_tokens=config.MAX_TOKENS, system=system, messages=messages)
        if tools:
            kwargs["tools"] = tools
        for attempt in range(max_retries + 1):
            try:
                response = self._client.messages.create(**kwargs)
                return {"content": [self._plain(b) for b in response.content]}
            except (anthropic.RateLimitError, anthropic.APIStatusError, anthropic.APIConnectionError) as e:
                last_err = e
                if attempt == max_retries:
                    raise
                time.sleep(1.5 * (attempt + 1))
        raise last_err

    @staticmethod
    def _plain(block):
        return block.model_dump() if hasattr(block, "model_dump") else block

    def _ask_groq(self, system, messages, tools, max_retries):
        from openai import APIStatusError, APIConnectionError

        oa_messages = [{"role": "system", "content": system}]
        oa_messages.extend(_canonical_to_openai(messages))
        oa_tools = _tools_to_openai(tools) if tools else None

        kwargs = dict(model=config.GROQ_MODEL, messages=oa_messages)
        if oa_tools:
            kwargs["tools"] = oa_tools

        last_err = None
        for attempt in range(max_retries + 1):
            try:
                response = self._client.chat.completions.create(**kwargs)
                return {"content": _openai_message_to_blocks(response.choices[0].message)}
            except (APIStatusError, APIConnectionError) as e:
                last_err = e
                if attempt == max_retries:
                    raise
                time.sleep(1.5 * (attempt + 1))
        raise last_err

def _tools_to_openai(tools: list) -> list:
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
            },
        }
        for t in tools
    ]


def _canonical_to_openai(messages: list) -> list:
    out = []
    for msg in messages:
        role = msg["role"]
        blocks = msg.get("content", [])

        if role == "user":
            text_parts = [b["text"] for b in blocks if b.get("type") == "text"]
            tool_results = [b for b in blocks if b.get("type") == "tool_result"]

            if text_parts:
                out.append({"role": "user", "content": "\n".join(text_parts)})
            for tr in tool_results:
                out.append({
                    "role": "tool",
                    "tool_call_id": tr["tool_use_id"],
                    "content": str(tr.get("content", "")),
                })

        elif role == "assistant":
            text_parts = [b["text"] for b in blocks if b.get("type") == "text"]
            tool_uses = [b for b in blocks if b.get("type") == "tool_use"]

            msg_out = {"role": "assistant", "content": "\n".join(text_parts) or None}
            if tool_uses:
                msg_out["tool_calls"] = [
                    {
                        "id": tu["id"],
                        "type": "function",
                        "function": {
                            "name": tu["name"],
                            "arguments": json.dumps(tu.get("input", {}), ensure_ascii=False),
                        },
                    }
                    for tu in tool_uses
                ]
            out.append(msg_out)

    return out


def _openai_message_to_blocks(message) -> list:
    blocks = []
    if message.content and message.content.strip():
        blocks.append({"type": "text", "text": message.content})

    for tc in (message.tool_calls or []):
        try:
            args = json.loads(tc.function.arguments or "{}")
        except json.JSONDecodeError:
            args = {}
        blocks.append({
            "type": "tool_use",
            "id": tc.id,
            "name": tc.function.name,
            "input": args,
        })
    return blocks


_client_singleton: ModelClient | None = None


def ask_model(system: str, messages: list, tools: list) -> dict:
    global _client_singleton
    if _client_singleton is None:
        _client_singleton = ModelClient()
    return _client_singleton.ask(system, messages, tools)
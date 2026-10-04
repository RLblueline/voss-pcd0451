"""Claude conversation with a tool-use loop and short rolling history."""
import logging

from . import config, persona

log = logging.getLogger("voss.brain")

FALLBACK = "[neutral] I can't reach head office right now, Employee. Please try again in a moment."


def _block_dict(b):
    if b.type == "text":
        return {"type": "text", "text": b.text}
    if b.type == "tool_use":
        return {"type": "tool_use", "id": b.id, "name": b.name, "input": b.input}
    return None


class Brain:
    def __init__(self, toolbox, client=None):
        if client is None:
            import anthropic
            client = anthropic.Anthropic(timeout=config.API_TIMEOUT_S, max_retries=1)
        self.client = client
        self.toolbox = toolbox
        self.history = []            # plain-text user/assistant messages only

    def _remember(self, user, assistant):
        self.history += [{"role": "user", "content": user},
                         {"role": "assistant", "content": assistant}]
        self.history = self.history[-2 * config.HISTORY_TURNS:]

    def reset(self):
        self.history = []

    def ask(self, user_text, on_tool=None):
        """Return (mood, gesture, spoken_text, tools_used)."""
        messages = self.history + [{"role": "user", "content": user_text}]
        used = []
        final = None
        try:
            for _ in range(config.MAX_TOOL_ROUNDS):
                resp = self.client.messages.create(
                    model=config.MODEL, max_tokens=config.MAX_TOKENS,
                    system=persona.system_prompt(), tools=self.toolbox.schemas,
                    messages=messages)
                text = " ".join(b.text for b in resp.content if b.type == "text").strip()
                if resp.stop_reason != "tool_use":
                    final = text
                    break
                messages.append({"role": "assistant",
                                 "content": [d for d in map(_block_dict, resp.content) if d]})
                results = []
                for b in resp.content:
                    if b.type != "tool_use":
                        continue
                    used.append(b.name)
                    if on_tool:
                        on_tool(b.name, b.input)
                    out = self.toolbox.dispatch(b.name, b.input)
                    log.info("tool %s(%s) -> %s", b.name, b.input, out[:200])
                    results.append({"type": "tool_result", "tool_use_id": b.id, "content": out})
                messages.append({"role": "user", "content": results})
        except Exception:
            log.exception("Claude request failed")
            final = None
        if not final:
            mood, gesture, spoken = persona.parse_tags(FALLBACK)
            return mood, gesture, spoken, used
        mood, gesture, spoken = persona.parse_tags(final)
        self._remember(user_text, f"[{mood}]" + (f" [{gesture}]" if gesture else "") + f" {spoken}")
        return mood, gesture, spoken, used

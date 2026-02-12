from typing import Dict, Any
import json

from prompts import SYSTEM_PROMPT
from tools import TOOLS


class DummyAgent:
    def __init__(self, client):
        self.client = client

    def call_llm(self, messages, stop=None) -> str:
        resp = self.client.chat.completions.create(
            model="moonshotai/Kimi-K2.5",
            messages=messages,
            max_tokens=400,
            stop=stop,
            stream=False,
            extra_body={"thinking": {"type": "disabled"}},
        )
        content = resp.choices[0].message.content
        return (content or "").strip()

    def extract_json(self, text: str) -> Dict[str, Any]:
        # Case 1: ```json ... ```
        start = text.find("```json")
        if start != -1:
            start = text.find("\n", start)
            end = text.find("```", start)
            raw = text[start:end].strip()
            return json.loads(raw)

        # Case 2: ``` ... ``` (no json tag)
        start = text.find("```")
        if start != -1:
            start = text.find("\n", start)
            end = text.find("```", start)
            raw = text[start:end].strip()
            if raw.startswith("{") and raw.endswith("}"):
                return json.loads(raw)

        # Case 3: First {...} anywhere
        first = text.find("{")
        last = text.rfind("}")
        if first != -1 and last != -1 and last > first:
            raw = text[first:last + 1].strip()
            return json.loads(raw)

        raise ValueError("No JSON found in model output")

    def run(self, question: str, max_steps: int = 5) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]

        for _ in range(max_steps):
            assistant_text = self.call_llm(messages, stop=["Observation:"])

            if not assistant_text:
                return "Final Answer: Model returned empty output."

            if "Final Answer:" in assistant_text:
                return assistant_text

            # Extract tool call (with 1 retry forcing JSON-only)
            try:
                tool_call = self.extract_json(assistant_text)
            except ValueError:
                messages.append({"role": "assistant", "content": assistant_text})
                messages.append({
                    "role": "user",
                    "content": "Return ONLY the tool call JSON inside a ```json``` block. No other text."
                })
                assistant_text = self.call_llm(messages, stop=["Observation:"])
                tool_call = self.extract_json(assistant_text)

            action = tool_call.get("action")
            action_input = tool_call.get("action_input", {})

            if not isinstance(action, str):
                return f"Final Answer: Invalid tool call (missing action): {tool_call}"
            if not isinstance(action_input, dict):
                return f"Final Answer: Invalid tool call (action_input must be dict): {tool_call}"
            if action not in TOOLS:
                return f"Final Answer: Unknown tool '{action}'. Available: {list(TOOLS.keys())}"

            result = TOOLS[action](**action_input)

            # Append real observation
            messages.append({
                "role": "assistant",
                "content": assistant_text + "\nObservation:\n" + str(result)
            })

            messages.append({
            "role": "user",
            "content": "Now provide the final response. End with exactly: Final Answer: <answer>"
            })
            final = self.call_llm(messages)

            if "Final Answer:" in final:
                return final

            messages.append({"role": "assistant", "content": final})

        return "Final Answer: Reached step limit."

from typing import Any


def extract_text_content(message_content: Any) -> str:
    if isinstance(message_content, str):
        return message_content

    if isinstance(message_content, list):
        texts: list[str] = []
        for part in message_content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_value = part.get("text")
                if isinstance(text_value, str):
                    texts.append(text_value)
        return "\n".join(texts).strip()

    return ""


def extract_response_text(response: Any) -> str:
    choices = getattr(response, "choices", None)
    if choices is None and isinstance(response, dict):
        choices = response.get("choices")

    if not choices:
        raise RuntimeError("No choices found in model response.")

    first_choice = choices[0]
    message = getattr(first_choice, "message", None)
    if message is None and isinstance(first_choice, dict):
        message = first_choice.get("message")

    if message is None:
        raise RuntimeError("No message found in first choice.")

    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content")

    text = extract_text_content(content)
    if not text.strip():
        raise RuntimeError("Model response content is empty.")
    return text.strip()


def generate_response(model: str, system_prompt: str, user_prompt: str) -> str:
    import litellm

    response = litellm.completion(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return extract_response_text(response)

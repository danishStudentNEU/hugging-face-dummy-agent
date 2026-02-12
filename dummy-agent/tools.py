def get_weather(location: str) -> str:
    location = (location or "").strip()
    if not location:
        return "Error: location was empty."
    # Dummy result (replace with a real API later if you want)
    return f"The weather in {location} is sunny with low temperatures."


TOOLS = {
    "get_weather": get_weather,
}
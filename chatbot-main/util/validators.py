import re

def validate_openai_api_key(api_key: str) -> bool:
    if not api_key:
        return False
    
    pattern = r'^sk-[a-zA-Z0-9]{48}$'
    return bool(re.match(pattern, api_key))


def validate_model(model: str) -> bool:
    valid_models = ["gpt-4", "gpt-4-turbo", "gpt-4o-mini"]
    return model in valid_models


def validate_max_tokens(max_tokens: int) -> bool:
    return 1 <= max_tokens <= 4096 


def validate_temperature(temperature: float) -> bool:
    return 0.0 <= temperature <= 2.0

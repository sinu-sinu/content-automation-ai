import json
from typing import Dict
import os


def load_brand_voice(channel_name: str, config_dir: str = "config") -> Dict:
    """
    Load brand voice profile for any channel (flexible for multiple channels).

    Args:
        channel_name: Name of the channel (e.g., "fireship", "veritasium", "astrum")
        config_dir: Directory containing brand profile JSON files

    Returns:
        Dictionary with brand voice characteristics

    Example:
        fireship_profile = load_brand_voice("fireship")
        veritasium_profile = load_brand_voice("veritasium")
    """
    # Convert channel name to filename (fireship -> fireship_brand_voice.json)
    filename = f"{channel_name.lower()}_brand_voice.json"
    filepath = os.path.join(config_dir, filename)

    try:
        with open(filepath, 'r') as f:
            profile = json.load(f)

        # Validate required fields exist
        required_fields = ['tone', 'formality_level', 'pacing', 'signature_phrases', 'avoid']
        missing = [field for field in required_fields if field not in profile]

        if missing:
            raise ValueError(f"Brand profile missing required fields: {missing}")

        return profile

    except FileNotFoundError:
        raise FileNotFoundError(
            f"Brand profile not found: {filepath}\n"
            f"Expected: config/{filename}"
        )
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {filepath}: {e}")
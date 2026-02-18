"""
Fetch Available Models from the GitHub Copilot API

Run this script to refresh the local cached list of available models.
The app reads from the generated JSON file so users see up-to-date model options.

Usage:
    python fetch_models.py
"""

import json
import os
import sys
from datetime import datetime, timezone

import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(SCRIPT_DIR, "copilot-api", "settings.json")
MODELS_FILE = os.path.join(SCRIPT_DIR, "copilot-api", "available_models.json")
API_URL = "https://api.githubcopilot.com/models"


def load_settings():
    """Load the GitHub PAT from settings."""
    if not os.path.exists(SETTINGS_FILE):
        print(f"Error: Settings file not found at {SETTINGS_FILE}")
        print("Please configure your GitHub PAT in the app settings first.")
        sys.exit(1)

    with open(SETTINGS_FILE, "r") as f:
        settings = json.load(f)

    pat = settings.get("github_pat", "")
    if not pat or pat in ("your-github-pat-here", ""):
        print("Error: No GitHub PAT configured in settings.json")
        sys.exit(1)

    return pat


def fetch_models(pat):
    """Query the Copilot API for available models."""
    headers = {
        "Authorization": f"Bearer {pat}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Copilot-Integration-Id": "copilot-chat",
    }

    print(f"Fetching models from {API_URL} ...")
    response = requests.get(API_URL, headers=headers, timeout=30)

    if response.status_code == 401:
        print("Error: Unauthorized. Check that your GitHub PAT is valid and has Copilot access.")
        sys.exit(1)
    elif response.status_code != 200:
        print(f"Error: API returned status {response.status_code}")
        print(response.text[:500])
        sys.exit(1)

    data = response.json()
    return data.get("data", [])


def process_models(raw_models):
    """
    Filter and deduplicate models, keeping only those that support /chat/completions.
    Returns a clean list sorted by vendor and category for the UI.
    """
    seen_ids = set()
    chat_models = []

    for m in raw_models:
        model_id = m["id"]
        model_type = m.get("capabilities", {}).get("type", "")
        endpoints = m.get("supported_endpoints", [])

        # Skip duplicates
        if model_id in seen_ids:
            continue
        seen_ids.add(model_id)

        # Skip non-chat models (embeddings, etc.)
        if model_type != "chat":
            continue

        # Only include models that support the /chat/completions endpoint
        # If supported_endpoints is empty/missing, assume it supports chat
        # (older models don't list endpoints but still work via /chat/completions)
        if endpoints and "/chat/completions" not in endpoints:
            continue

        # Skip custom/fine-tuned org models
        if m.get("custom_model"):
            continue

        limits = m.get("capabilities", {}).get("limits", {})
        supports = m.get("capabilities", {}).get("supports", {})

        chat_models.append({
            "id": model_id,
            "name": m.get("name", model_id),
            "vendor": m.get("vendor", "Unknown"),
            "version": m.get("version", ""),
            "family": m.get("capabilities", {}).get("family", ""),
            "category": m.get("model_picker_category", ""),
            "preview": m.get("preview", False),
            "model_picker_enabled": m.get("model_picker_enabled", False),
            "max_context_window_tokens": limits.get("max_context_window_tokens"),
            "max_output_tokens": limits.get("max_output_tokens"),
            "max_prompt_tokens": limits.get("max_prompt_tokens"),
            "supports_vision": supports.get("vision", False),
            "supports_streaming": supports.get("streaming", False),
            "supports_tool_calls": supports.get("tool_calls", False),
        })

    # Sort: picker-enabled first, then by vendor, then by name
    category_order = {"powerful": 0, "versatile": 1, "lightweight": 2, "": 3}
    chat_models.sort(key=lambda m: (
        not m["model_picker_enabled"],
        m["vendor"],
        category_order.get(m["category"], 3),
        m["name"],
    ))

    return chat_models


def build_display_name(model):
    """Build a human-readable display name for the model dropdown."""
    name = model["name"]
    vendor = model["vendor"]
    category = model["category"]

    # Simplify vendor names
    vendor_short = vendor
    if "Azure" in vendor:
        vendor_short = "OpenAI"

    parts = [name]
    label_parts = []
    if vendor_short:
        label_parts.append(vendor_short)
    if category:
        label_parts.append(category.capitalize())
    if model["preview"]:
        label_parts.append("Preview")

    if label_parts:
        parts.append(f"({', '.join(label_parts)})")

    return " ".join(parts)


def save_models(chat_models):
    """Save the processed model list to a JSON file."""
    # Add display_name for each model
    for m in chat_models:
        m["display_name"] = build_display_name(m)

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "model_count": len(chat_models),
        "models": chat_models,
    }

    os.makedirs(os.path.dirname(MODELS_FILE), exist_ok=True)
    with open(MODELS_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved {len(chat_models)} models to {MODELS_FILE}")
    return output


def main():
    pat = load_settings()
    raw_models = fetch_models(pat)
    print(f"API returned {len(raw_models)} total models")

    chat_models = process_models(raw_models)
    output = save_models(chat_models)

    # Print summary table
    print(f"\n{'ID':<35} {'Display Name':<50} {'Context':>8}")
    print("-" * 95)
    for m in output["models"]:
        ctx = m.get("max_context_window_tokens", "")
        ctx_str = f"{ctx:,}" if ctx else "N/A"
        print(f"{m['id']:<35} {m['display_name']:<50} {ctx_str:>8}")


if __name__ == "__main__":
    main()

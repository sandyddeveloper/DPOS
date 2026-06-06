"""
CRUD for saved workspaces.
"""
import os
import json
from config import RESOURCE_DIR

TEMPLATES_DIR = os.path.join(RESOURCE_DIR, "modules", "workspace", "templates")

def list_templates() -> list[dict]:
    """List all available workspace templates from the templates directory."""
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    templates = []
    for filename in os.listdir(TEMPLATES_DIR):
        if filename.endswith(".json"):
            path = os.path.join(TEMPLATES_DIR, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    templates.append(data)
            except Exception as e:
                print(f"Error reading template {filename}: {e}")
    return templates

def get_template(name: str) -> dict:
    """Retrieve a workspace template configuration by name (case-insensitive)."""
    for t in list_templates():
        if t.get("name", "").lower() == name.lower():
            return t
    return None

def save_template(name: str, description: str, services: list) -> bool:
    """Save a new template configuration to a JSON file."""
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    safe_name = "".join([c if c.isalnum() else "_" for c in name]).lower()
    path = os.path.join(TEMPLATES_DIR, f"{safe_name}.json")
    try:
        data = {
            "name": name,
            "description": description,
            "services": services
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving template {name}: {e}")
        return False

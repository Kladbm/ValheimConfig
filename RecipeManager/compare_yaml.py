#!/usr/bin/env python3
"""
YAML Recipe Comparator
Compares only crafting ingredients between two YAML files.
"""

import yaml
import sys


def load_yaml(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def extract_items(data: dict) -> dict:
    for key, value in data.items():
        if isinstance(value, dict):
            return value
    return {}


def get_ingredients(item: dict) -> list:
    """Extract ingredients list from item, regardless of structure."""
    # recipeModifications style: item.recipe.ingredients
    if "recipe" in item and isinstance(item["recipe"], dict):
        return item["recipe"].get("ingredients", [])
    # pieceModifications style: item.requirements
    if "requirements" in item:
        return item["requirements"]
    return []


def normalize_ingredients(ingredients: list) -> set:
    """Convert list of ingredients to a comparable set of tuples."""
    result = set()
    for ing in ingredients:
        # Handle both craftCost and amount fields
        cost = ing.get("craftCost") or ing.get("amount")
        result.add((ing.get("prefab"), cost))
    return result


def compare_files(file1: str, file2: str):
    print(f"\nLoading '{file1}' (source)...")
    items1 = extract_items(load_yaml(file1))

    print(f"Loading '{file2}' (reference)...")
    items2 = extract_items(load_yaml(file2))

    print(f"\nItems in source: {len(items1)} | Items in reference: {len(items2)}\n")
    print("=" * 60)

    matched = []
    different = []
    not_found = []

    for name, item1 in items1.items():
        # Search by prefab name, not key name
        prefab = item1.get("prefab")
        
        # Find matching item in file2 (by key or by prefab)
        item2 = None
        if name in items2:
            item2 = items2[name]
        else:
            # Try to find by prefab
            for key2, val2 in items2.items():
                if val2.get("prefab") == prefab:
                    item2 = val2
                    break

        if item2 is None:
            not_found.append(name)
            continue

        ing1 = normalize_ingredients(get_ingredients(item1))
        ing2 = normalize_ingredients(get_ingredients(item2))

        if ing1 == ing2:
            matched.append((name, item1))
        else:
            different.append((name, ing1, ing2))

    # Print matches
    for name, item in matched:
        print(f"✅  MATCH: {name}")
        print("-" * 60)
        print(yaml.dump({name: item}, allow_unicode=True,
                        default_flow_style=False, sort_keys=False))
        print("-" * 60)

    # Summary
    print("=" * 60)
    print(f"\n📊 Summary:")
    print(f"   Matched (same ingredients): {len(matched)}")
    print(f"   Different ingredients:      {len(different)}")
    print(f"   Not found in reference:     {len(not_found)}")

    if different:
        print(f"\n⚠️  Different ingredients:")
        for name, ing1, ing2 in different:
            print(f"\n   [{name}]")
            print(f"   Source:    {sorted(ing1)}")
            print(f"   Reference: {sorted(ing2)}")

    if not_found:
        print(f"\n❌  Not found in reference:")
        for name in not_found:
            print(f"   - {name}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare_yaml.py file1.yaml file2.yaml")
        sys.exit(1)
    compare_files(sys.argv[1], sys.argv[2])
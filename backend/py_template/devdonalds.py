import re
from dataclasses import dataclass
from typing import Dict, List, Union

from flask import Flask, jsonify, request


# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
    name: str


@dataclass
class RequiredItem:
    name: str
    quantity: int


@dataclass
class Recipe(CookbookEntry):
    required_items: List[RequiredItem]


@dataclass
class Ingredient(CookbookEntry):
    cook_time: int


# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here!
cookbook: Dict[str, CookbookEntry] = {}


# Task 1 helper (don't touch)
@app.route("/parse", methods=["POST"])
def parse():
    data = request.get_json()
    recipe_name = data.get("input", "")
    parsed_name = parse_handwriting(recipe_name)
    if parsed_name is None:
        return "Invalid recipe name", 400
    return jsonify({"msg": parsed_name}), 200


# [TASK 1] ====================================================================
# Takes in a recipeName and returns it in a form that
# why no option type wryyyyyy
def parse_handwriting(recipeName: str) -> Union[str | None]:
    new_name = recipeName.replace("-", " ").replace("_", " ")
    new_name = " ".join(new_name.split())
    new_name = "".join([c for c in new_name if c.isalpha() or c.isspace()])
    new_name = new_name.title()
    return new_name if new_name else None


# [TASK 2] ====================================================================
# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route("/entry", methods=["POST"])
def create_entry():
    data = request.get_json()

    entry_name = data.get("name")
    if not isinstance(entry_name, str) or entry_name in cookbook:
        return jsonify({"error": "Name must be unique"}), 400

    match data.get("type", ""):
        case "recipe":
            required_items_data = data.get("requiredItems", [])
            if not isinstance(required_items_data, list):
                return jsonify({"error": "Invalid requiredItems format"}), 400

            seen_items = set()
            required_items = []

            for item in required_items_data:
                if (
                    not isinstance(item, dict)
                    or "name" not in item
                    or "quantity" not in item
                ):
                    return jsonify({"error": "Invalid requiredItems format"}), 400

                item_name = item["name"]
                if item_name in seen_items:
                    return jsonify({"error": "Duplicate item in requiredItems"}), 400

                seen_items.add(item_name)
                required_items.append(
                    RequiredItem(name=item_name, quantity=item["quantity"])
                )

            cookbook[entry_name] = Recipe(
                name=entry_name, required_items=required_items
            )
        case "ingredient":
            cook_time = data.get("cookTime")
            if not isinstance(cook_time, int) or cook_time < 0:
                return jsonify({"error": "Invalid cookTime"}), 400
            cookbook[entry_name] = Ingredient(name=entry_name, cook_time=cook_time)

        case _:
            return "Invalid Type", 400
    return "", 200


# [TASK 3] ====================================================================


def get_recipe_summary(recipe_name: str, quantity: int):
    if recipe_name not in cookbook or isinstance(cookbook[recipe_name], Ingredient):
        return None, None, 400
    recipe = cookbook[recipe_name]
    cook_time = 0
    ingredients = {}
    for item in recipe.required_items:
        if item.name not in cookbook:
            return None, None, 400
        if isinstance(cookbook[item.name], Ingredient):
            ingredients[item.name] = (
                ingredients.get(item.name, 0) + item.quantity * quantity
            )
            cook_time += item.quantity * quantity * cookbook[item.name].cook_time
        elif isinstance(cookbook[item.name], Recipe):
            a, b, c = get_recipe_summary(item.name, item.quantity * quantity)
            if c == 400:
                return None, None, 400
            cook_time += a
            combined_dict = {}
            for key in set(ingredients) | set(b):
                combined_dict[key] = ingredients.get(key, 0) + b.get(key, 0)
            ingredients = combined_dict

    return cook_time, ingredients, 200


# Endpoint that returns a summary of a recipe that corresponds to a query name
@app.route("/summary", methods=["GET"])
def summary():
    recipe_name = request.args.get("name")

    if not recipe_name:
        return jsonify({"error": "Recipe name is required"}), 400

    cook_time, ingredients, status_code = get_recipe_summary(recipe_name, 1)

    if status_code == 400:
        return jsonify({"error": "Invalid recipe request"}), 400

    ingredient_list = [
        {"name": key, "quantity": val} for key, val in ingredients.items()
    ]
    result = {
        "name": recipe_name,
        "cookTime": cook_time,
        "ingredients": ingredient_list,
    }

    return jsonify(result), 200


# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == "__main__":
    app.run(debug=True, port=8080)

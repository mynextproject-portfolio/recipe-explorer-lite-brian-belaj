from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Optional
import json
from app.models import Recipe, RecipeCreate, RecipeUpdate
from app.services.storage import recipe_storage

router = APIRouter(prefix="/api")


def normalize_recipe(recipe):
    if not recipe:
        return recipe

    if isinstance(recipe.instructions, str):
        recipe.instructions = [
            step.strip() for step in recipe.instructions.split("\n") if step.strip()
        ]

    if not getattr(recipe, "cuisine", None):
        recipe.cuisine = "Other"

    return recipe


@router.get("/recipes")
def get_recipes(search: Optional[str] = None):
    """Get all recipes or search by title"""
    if search:
        recipes = recipe_storage.search_recipes(search)
    else:
        recipes = recipe_storage.get_all_recipes()

    recipes = [normalize_recipe(recipe) for recipe in recipes]

    print(f"Returning {len(recipes)} recipes")

    return {"recipes": jsonable_encoder(recipes)}


@router.get("/recipes/export")
def export_recipes():
    """Export all recipes as JSON"""
    recipes = recipe_storage.get_all_recipes()
    recipes = [normalize_recipe(recipe) for recipe in recipes]
    return JSONResponse(content=jsonable_encoder(recipes))


@router.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: str):
    """Get a specific recipe by ID"""
    recipe = recipe_storage.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    recipe = normalize_recipe(recipe)
    return jsonable_encoder(recipe)


@router.post("/recipes")
def create_recipe(recipe: RecipeCreate):
    """Create a new recipe"""
    new_recipe = recipe_storage.create_recipe(recipe)
    new_recipe = normalize_recipe(new_recipe)
    return jsonable_encoder(new_recipe)


@router.put("/recipes/{recipe_id}")
def update_recipe(recipe_id: str, recipe: RecipeUpdate):
    """Update an existing recipe"""
    updated_recipe = recipe_storage.update_recipe(recipe_id, recipe)
    if not updated_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    updated_recipe = normalize_recipe(updated_recipe)
    return jsonable_encoder(updated_recipe)


@router.delete("/recipes/{recipe_id}")
def delete_recipe(recipe_id: str):
    """Delete a recipe"""
    success = recipe_storage.delete_recipe(recipe_id)
    if not success:
        return {"error": "Recipe not found", "status": "failed"}
    return {"message": "Recipe deleted successfully", "status": "success"}


@router.post("/recipes/import")
async def import_recipes(file: UploadFile = File(...)):
    """Import recipes from JSON file"""
    try:
        content = await file.read()

        if len(content) > 1000000:
            return {"error": "File too large"}

        recipes_data = json.loads(content)

        if not isinstance(recipes_data, list):
            raise HTTPException(status_code=400, detail="JSON must be an array of recipes")

        for recipe in recipes_data:
            if isinstance(recipe.get("instructions"), str):
                recipe["instructions"] = [
                    step.strip()
                    for step in recipe["instructions"].split("\n")
                    if step.strip()
                ]

            if not recipe.get("cuisine"):
                recipe["cuisine"] = "Other"

        print(f"Importing {len(recipes_data)} recipes from {file.filename}")

        count = recipe_storage.import_recipes(recipes_data)

        return {"message": f"Successfully imported {count} recipes", "count": count}

    except json.JSONDecodeError as e:
        print(f"JSON error: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

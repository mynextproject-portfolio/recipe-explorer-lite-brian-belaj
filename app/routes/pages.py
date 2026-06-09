from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from app.models import RecipeCreate, RecipeUpdate
from app.services.storage import recipe_storage

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


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


@router.get("/", response_class=HTMLResponse)
def home(request: Request, search: Optional[str] = None, message: Optional[str] = None):
    """Home page with recipe list and search"""
    if search:
        recipes = recipe_storage.search_recipes(search)
    else:
        recipes = recipe_storage.get_all_recipes()

    recipes = [normalize_recipe(recipe) for recipe in recipes]

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "recipes": recipes,
            "search_query": search or "",
            "message": message,
        },
    )


@router.get("/recipes/new", response_class=HTMLResponse)
def new_recipe_form(request: Request):
    """New recipe form"""
    return templates.TemplateResponse(
        request,
        "recipe_form.html",
        {"request": request, "recipe": None, "is_edit": False},
    )


@router.get("/recipes/{recipe_id}", response_class=HTMLResponse)
def recipe_detail(request: Request, recipe_id: str, message: Optional[str] = None):
    """Recipe detail page"""
    recipe = recipe_storage.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    recipe = normalize_recipe(recipe)

    return templates.TemplateResponse(
        request,
        "recipe_detail.html",
        {"request": request, "recipe": recipe, "message": message},
    )


@router.get("/recipes/{recipe_id}/edit", response_class=HTMLResponse)
def edit_recipe_form(request: Request, recipe_id: str):
    """Edit recipe form"""
    recipe = recipe_storage.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    recipe = normalize_recipe(recipe)

    return templates.TemplateResponse(
        request,
        "recipe_form.html",
        {"request": request, "recipe": recipe, "is_edit": True},
    )


@router.post("/recipes/new")
def create_recipe_form(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    difficulty: str = Form(...),
    ingredients: str = Form(...),
    instructions: str = Form(...),
    cuisine: str = Form(...),
    tags: str = Form(...),
):
    """Handle new recipe form submission"""
    try:
        if len(title) > 200:
            raise ValueError("Title too long")

        ingredient_list = [
            ing.strip() for ing in ingredients.split("\n") if ing.strip()
        ]
        instruction_steps = [
            step.strip() for step in instructions.split("\n") if step.strip()
        ]
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        if len(ingredient_list) == 0:
            raise ValueError("At least one ingredient required")

        if len(instruction_steps) == 0:
            raise ValueError("At least one instruction step is required")

        if not cuisine.strip():
            raise ValueError("Cuisine is required")

        recipe_data = RecipeCreate(
            title=title.strip(),
            description=description.strip(),
            difficulty=difficulty.strip(),
            ingredients=ingredient_list,
            instructions=instruction_steps,
            tags=tag_list,
            cuisine=cuisine.strip(),
        )

        new_recipe = recipe_storage.create_recipe(recipe_data)
        return RedirectResponse(
            url=f"/recipes/{new_recipe.id}?message=Recipe created successfully",
            status_code=303,
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/?message=Error creating recipe: {str(e)}",
            status_code=303,
        )


@router.post("/recipes/{recipe_id}/edit")
def update_recipe_form(
    request: Request,
    recipe_id: str,
    title: str = Form(...),
    description: str = Form(...),
    difficulty: str = Form(...),
    ingredients: str = Form(...),
    instructions: str = Form(...),
    cuisine: str = Form(...),
    tags: str = Form(...),
):
    """Handle edit recipe form submission"""
    try:
        if len(title) > 200:
            raise ValueError("Title is too long!")

        ingredient_list = [
            ing.strip() for ing in ingredients.split("\n") if ing.strip()
        ]
        instruction_steps = [
            step.strip() for step in instructions.split("\n") if step.strip()
        ]
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        if len(ingredient_list) == 0:
            raise ValueError("Need ingredients!")

        if len(instruction_steps) == 0:
            raise ValueError("At least one instruction step is required")

        if not cuisine.strip():
            raise ValueError("Cuisine is required")

        recipe_data = RecipeUpdate(
            title=title.strip(),
            description=description.strip(),
            difficulty=difficulty.strip(),
            ingredients=ingredient_list,
            instructions=instruction_steps,
            tags=tag_list,
            cuisine=cuisine.strip(),
        )

        updated_recipe = recipe_storage.update_recipe(recipe_id, recipe_data)
        if not updated_recipe:
            return RedirectResponse(
                url="/?message=Recipe not found",
                status_code=303,
            )

        return RedirectResponse(
            url=f"/recipes/{recipe_id}?message=Recipe updated successfully",
            status_code=303,
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/recipes/{recipe_id}?message=Error updating recipe: {str(e)}",
            status_code=303,
        )


@router.post("/recipes/{recipe_id}/delete")
def delete_recipe_form(recipe_id: str):
    """Handle recipe deletion"""
    success = recipe_storage.delete_recipe(recipe_id)
    if success:
        return RedirectResponse(
            url="/?message=Recipe deleted successfully",
            status_code=303,
        )
    else:
        return RedirectResponse(
            url="/?message=Recipe not found",
            status_code=303,
        )


@router.get("/import", response_class=HTMLResponse)
def import_page(request: Request, message: Optional[str] = None):
    """Import recipes page"""
    return templates.TemplateResponse(
        request,
        "import.html",
        {"request": request, "message": message},
    )

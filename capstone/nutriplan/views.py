import json
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST, require_GET

from .forms import RegisterForm, RecipeForm, IngredientForm, RecipeIngredientForm, UserProfileForm
from .models import Recipe, Ingredient, RecipeIngredient, MealPlanEntry, DietaryTag, UserProfile, CUISINE_CHOICES, MEAL_SLOTS


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, f'Welcome, {user.username}!')
            return redirect('index')
    else:
        form = RegisterForm()
    return render(request, 'nutriplan/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(request.GET.get('next', 'index'))
    else:
        form = AuthenticationForm()
    return render(request, 'nutriplan/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('index')


# ---------------------------------------------------------------------------
# Landing
# ---------------------------------------------------------------------------

def index(request):
    recent = Recipe.objects.select_related('user').prefetch_related('tags')[:6]
    return render(request, 'nutriplan/index.html', {'recent_recipes': recent})


# ---------------------------------------------------------------------------
# Recipes
# ---------------------------------------------------------------------------

def recipe_list(request):
    recipes = Recipe.objects.select_related('user').prefetch_related('tags', 'recipeingredient_set__ingredient')
    if request.user.is_authenticated:
        mine = request.GET.get('mine')
        if mine:
            recipes = recipes.filter(user=request.user)

    cuisine = request.GET.get('cuisine', '')
    tag_ids = request.GET.getlist('tags')
    max_time = request.GET.get('max_time', '')

    if cuisine:
        recipes = recipes.filter(cuisine=cuisine)
    if tag_ids:
        for tid in tag_ids:
            recipes = recipes.filter(tags__id=tid)
    if max_time:
        try:
            t = int(max_time)
            # filter where prep+cook <= t (annotate workaround via Python)
            recipes = [r for r in recipes if r.total_time <= t]
        except ValueError:
            pass

    context = {
        'recipes': recipes,
        'tags': DietaryTag.objects.all(),
        'cuisines': CUISINE_CHOICES,
        'selected_cuisine': cuisine,
        'selected_tags': [int(i) for i in tag_ids if i.isdigit()],
        'max_time': max_time,
    }
    return render(request, 'nutriplan/recipes.html', context)


def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    nutrition = recipe.nutrition_per_serving()
    ingredients = recipe.recipeingredient_set.select_related('ingredient').all()
    return render(request, 'nutriplan/recipe_detail.html', {
        'recipe': recipe,
        'nutrition': nutrition,
        'ingredients': ingredients,
    })


@login_required
def recipe_create(request):
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.user = request.user
            recipe.save()
            form.save_m2m()
            messages.success(request, 'Recipe created!')
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        form = RecipeForm()
    return render(request, 'nutriplan/recipe_form.html', {'form': form, 'action': 'Create'})


@login_required
def recipe_edit(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, user=request.user)
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        if form.is_valid():
            form.save()
            messages.success(request, 'Recipe updated!')
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        form = RecipeForm(instance=recipe)
    return render(request, 'nutriplan/recipe_form.html', {
        'form': form, 'action': 'Edit', 'recipe': recipe
    })


@login_required
def recipe_delete(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, user=request.user)
    if request.method == 'POST':
        recipe.delete()
        messages.success(request, 'Recipe deleted.')
        return redirect('recipe_list')
    return render(request, 'nutriplan/recipe_confirm_delete.html', {'recipe': recipe})


# ---------------------------------------------------------------------------
# Ingredients
# ---------------------------------------------------------------------------

@login_required
def ingredient_list(request):
    ingredients = Ingredient.objects.all().order_by('name')
    return render(request, 'nutriplan/ingredient_list.html', {'ingredients': ingredients})


@login_required
def ingredient_create(request):
    if request.method == 'POST':
        form = IngredientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ingredient added!')
            return redirect('ingredient_list')
    else:
        form = IngredientForm()
    return render(request, 'nutriplan/ingredient_form.html', {'form': form})


@login_required
def add_recipe_ingredient(request, recipe_pk):
    recipe = get_object_or_404(Recipe, pk=recipe_pk, user=request.user)
    if request.method == 'POST':
        form = RecipeIngredientForm(request.POST)
        if form.is_valid():
            ri = form.save(commit=False)
            ri.recipe = recipe
            try:
                ri.save()
                messages.success(request, 'Ingredient added to recipe.')
            except IntegrityError:
                messages.error(request, 'That ingredient is already in this recipe.')
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        form = RecipeIngredientForm()
    return render(request, 'nutriplan/add_ingredient.html', {'form': form, 'recipe': recipe})


@login_required
def remove_recipe_ingredient(request, recipe_pk, ri_pk):
    recipe = get_object_or_404(Recipe, pk=recipe_pk, user=request.user)
    ri = get_object_or_404(RecipeIngredient, pk=ri_pk, recipe=recipe)
    ri.delete()
    messages.success(request, 'Ingredient removed.')
    return redirect('recipe_detail', pk=recipe.pk)


# ---------------------------------------------------------------------------
# Meal Planner
# ---------------------------------------------------------------------------

@login_required
def planner(request):
    # Determine week start (Monday)
    today = date.today()
    week_offset = int(request.GET.get('week', 0))
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    week_days = [monday + timedelta(days=i) for i in range(7)]

    entries = MealPlanEntry.objects.filter(
        user=request.user,
        date__gte=monday,
        date__lte=week_days[-1],
    ).select_related('recipe')

    # Build grid: {date: {slot: [entries]}}
    grid = {}
    for d in week_days:
        grid[d] = {slot[0]: [] for slot in MEAL_SLOTS}
    for entry in entries:
        grid[entry.date][entry.meal_slot].append(entry)

    # Compute daily nutrition totals
    daily_nutrition = {}
    for d in week_days:
        totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
        for slot_entries in grid[d].values():
            for e in slot_entries:
                n = e.recipe.nutrition_per_serving()
                for key in totals:
                    totals[key] += n.get(key, 0)
        daily_nutrition[d] = {k: round(v, 1) for k, v in totals.items()}

    # Profile for calorie goal
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    user_recipes = Recipe.objects.filter(user=request.user).prefetch_related('recipeingredient_set__ingredient')

    context = {
        'week_days': week_days,
        'grid': grid,
        'meal_slots': MEAL_SLOTS,
        'daily_nutrition': daily_nutrition,
        'week_offset': week_offset,
        'today': today,
        'user_recipes': user_recipes,
        'calorie_goal': profile.daily_calorie_goal,
    }
    return render(request, 'nutriplan/planner.html', context)


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'nutriplan/profile.html', {'form': form, 'profile': profile})


# ---------------------------------------------------------------------------
# JSON API
# ---------------------------------------------------------------------------

@login_required
def api_recipes(request):
    """Return filtered recipes as JSON for the recipe sidebar search."""
    recipes = Recipe.objects.filter(user=request.user).prefetch_related(
        'tags', 'recipeingredient_set__ingredient'
    )
    q = request.GET.get('q', '').strip()
    cuisine = request.GET.get('cuisine', '')
    if q:
        recipes = recipes.filter(title__icontains=q)
    if cuisine:
        recipes = recipes.filter(cuisine=cuisine)

    data = []
    for r in recipes:
        n = r.nutrition_per_serving()
        data.append({
            'id': r.id,
            'title': r.title,
            'cuisine': r.get_cuisine_display(),
            'total_time': r.total_time,
            'calories': n['calories'],
            'protein': n['protein'],
            'carbs': n['carbs'],
            'fat': n['fat'],
            'image': r.image.url if r.image else None,
        })
    return JsonResponse({'recipes': data})


@login_required
@require_POST
def api_mealplan_add(request):
    try:
        body = json.loads(request.body)
        recipe_id = int(body['recipe_id'])
        entry_date = body['date']  # YYYY-MM-DD
        meal_slot = body['meal_slot']
    except (KeyError, ValueError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid payload'}, status=400)

    recipe = get_object_or_404(Recipe, pk=recipe_id)
    entry = MealPlanEntry.objects.create(
        user=request.user,
        recipe=recipe,
        date=entry_date,
        meal_slot=meal_slot,
    )
    nutrition = recipe.nutrition_per_serving()
    return JsonResponse({
        'id': entry.id,
        'recipe_id': recipe.id,
        'recipe_title': recipe.title,
        'date': str(entry.date),
        'meal_slot': entry.meal_slot,
        'nutrition': nutrition,
    }, status=201)


@login_required
@require_POST
def api_mealplan_remove(request):
    try:
        body = json.loads(request.body)
        entry_id = int(body['entry_id'])
    except (KeyError, ValueError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid payload'}, status=400)

    entry = get_object_or_404(MealPlanEntry, pk=entry_id, user=request.user)
    nutrition = entry.recipe.nutrition_per_serving()
    entry.delete()
    return JsonResponse({'deleted': entry_id, 'nutrition': nutrition})

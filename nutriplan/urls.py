from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Recipes
    path('recipes/', views.recipe_list, name='recipe_list'),
    path('recipes/create/', views.recipe_create, name='recipe_create'),
    path('recipes/<int:pk>/', views.recipe_detail, name='recipe_detail'),
    path('recipes/<int:pk>/edit/', views.recipe_edit, name='recipe_edit'),
    path('recipes/<int:pk>/delete/', views.recipe_delete, name='recipe_delete'),
    path('recipes/<int:recipe_pk>/ingredients/add/', views.add_recipe_ingredient, name='add_recipe_ingredient'),
    path('recipes/<int:recipe_pk>/ingredients/<int:ri_pk>/remove/', views.remove_recipe_ingredient, name='remove_recipe_ingredient'),

    # Ingredients
    path('ingredients/', views.ingredient_list, name='ingredient_list'),
    path('ingredients/create/', views.ingredient_create, name='ingredient_create'),

    # Meal Planner
    path('planner/', views.planner, name='planner'),

    # API
    path('api/recipes/', views.api_recipes, name='api_recipes'),
    path('api/mealplan/add/', views.api_mealplan_add, name='api_mealplan_add'),
    path('api/mealplan/remove/', views.api_mealplan_remove, name='api_mealplan_remove'),
]

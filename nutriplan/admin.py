from django.contrib import admin
from .models import Recipe, Ingredient, RecipeIngredient, MealPlanEntry, DietaryTag, UserProfile


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'cuisine', 'prep_time', 'cook_time', 'servings', 'created_at')
    list_filter = ('cuisine', 'tags')
    search_fields = ('title', 'user__username')
    inlines = [RecipeIngredientInline]


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'calories_per_100', 'protein_per_100', 'carbs_per_100', 'fat_per_100')
    search_fields = ('name',)


@admin.register(DietaryTag)
class DietaryTagAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(MealPlanEntry)
class MealPlanEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'date', 'meal_slot')
    list_filter = ('meal_slot', 'date')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'daily_calorie_goal')

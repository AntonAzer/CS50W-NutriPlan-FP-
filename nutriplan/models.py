from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


MEAL_SLOTS = [
    ('breakfast', 'Breakfast'),
    ('lunch', 'Lunch'),
    ('dinner', 'Dinner'),
    ('snack', 'Snack'),
]

CUISINE_CHOICES = [
    ('italian', 'Italian'),
    ('mexican', 'Mexican'),
    ('asian', 'Asian'),
    ('american', 'American'),
    ('mediterranean', 'Mediterranean'),
    ('indian', 'Indian'),
    ('middle_eastern', 'Middle Eastern'),
    ('other', 'Other'),
]

UNIT_CHOICES = [
    ('g', 'grams'),
    ('ml', 'millilitres'),
    ('cup', 'cup'),
    ('tbsp', 'tablespoon'),
    ('tsp', 'teaspoon'),
    ('piece', 'piece'),
    ('oz', 'oz'),
]


class DietaryTag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ingredient with nutritional values per 100 g / 100 ml."""
    name = models.CharField(max_length=100, unique=True)
    calories_per_100 = models.FloatField(default=0, validators=[MinValueValidator(0)])
    protein_per_100 = models.FloatField(default=0, validators=[MinValueValidator(0)])
    carbs_per_100 = models.FloatField(default=0, validators=[MinValueValidator(0)])
    fat_per_100 = models.FloatField(default=0, validators=[MinValueValidator(0)])

    def __str__(self):
        return self.name


class Recipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    cuisine = models.CharField(max_length=50, choices=CUISINE_CHOICES, default='other')
    prep_time = models.PositiveIntegerField(help_text='Minutes', default=15)
    cook_time = models.PositiveIntegerField(help_text='Minutes', default=30)
    servings = models.PositiveIntegerField(default=2, validators=[MinValueValidator(1)])
    instructions = models.TextField(blank=True)
    image = models.ImageField(upload_to='recipes/', blank=True, null=True)
    tags = models.ManyToManyField(DietaryTag, blank=True)
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient', related_name='recipes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def total_time(self):
        return self.prep_time + self.cook_time

    def nutrition_per_serving(self):
        """Return dict of nutritional totals divided by servings."""
        totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
        for ri in self.recipeingredient_set.select_related('ingredient').all():
            factor = ri.quantity / 100.0
            totals['calories'] += ri.ingredient.calories_per_100 * factor
            totals['protein'] += ri.ingredient.protein_per_100 * factor
            totals['carbs'] += ri.ingredient.carbs_per_100 * factor
            totals['fat'] += ri.ingredient.fat_per_100 * factor
        if self.servings:
            return {k: round(v / self.servings, 1) for k, v in totals.items()}
        return {k: round(v, 1) for k, v in totals.items()}


class RecipeIngredient(models.Model):
    """Through table: Recipe ↔ Ingredient with quantity & unit."""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.FloatField(validators=[MinValueValidator(0.1)])
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='g')

    class Meta:
        unique_together = ('recipe', 'ingredient')

    def __str__(self):
        return f'{self.quantity}{self.unit} {self.ingredient.name}'


class MealPlanEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_plan')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    date = models.DateField()
    meal_slot = models.CharField(max_length=20, choices=MEAL_SLOTS)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'meal_slot']

    def __str__(self):
        return f'{self.user.username} — {self.recipe.title} on {self.date} ({self.meal_slot})'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    daily_calorie_goal = models.PositiveIntegerField(default=2000)

    def __str__(self):
        return f'{self.user.username} profile'

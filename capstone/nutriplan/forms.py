from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column, Field
from .models import Recipe, Ingredient, RecipeIngredient, UserProfile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Create Account', css_class='btn btn-success w-100 mt-2'))


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['title', 'description', 'cuisine', 'prep_time', 'cook_time',
                  'servings', 'instructions', 'image', 'tags']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'instructions': forms.Textarea(attrs={'rows': 6}),
            'tags': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'title',
            Row(
                Column('cuisine', css_class='col-md-4'),
                Column('prep_time', css_class='col-md-4'),
                Column('cook_time', css_class='col-md-4'),
            ),
            'servings',
            'description',
            'instructions',
            'image',
            'tags',
        )
        self.helper.add_input(Submit('submit', 'Save Recipe', css_class='btn btn-primary mt-2'))


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['name', 'calories_per_100', 'protein_per_100', 'carbs_per_100', 'fat_per_100']
        labels = {
            'calories_per_100': 'Calories per 100g',
            'protein_per_100': 'Protein per 100g (g)',
            'carbs_per_100': 'Carbs per 100g (g)',
            'fat_per_100': 'Fat per 100g (g)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'name',
            Row(
                Column('calories_per_100', css_class='col-md-3'),
                Column('protein_per_100', css_class='col-md-3'),
                Column('carbs_per_100', css_class='col-md-3'),
                Column('fat_per_100', css_class='col-md-3'),
            ),
        )
        self.helper.add_input(Submit('submit', 'Save Ingredient', css_class='btn btn-primary mt-2'))


class RecipeIngredientForm(forms.ModelForm):
    class Meta:
        model = RecipeIngredient
        fields = ['ingredient', 'quantity', 'unit']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('ingredient', css_class='col-md-6'),
                Column('quantity', css_class='col-md-3'),
                Column('unit', css_class='col-md-3'),
            )
        )


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['daily_calorie_goal']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Save', css_class='btn btn-primary'))

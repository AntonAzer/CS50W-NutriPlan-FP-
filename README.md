# NutriPlan — Recipe & Weekly Meal Planner

NutriPlan is a full-stack web application built with Django and JavaScript that allows users to create, save, and organize recipes, then drag-and-drop them onto a weekly meal planner calendar. It also calculates nutritional totals for each planned day.

---

## Distinctiveness and Complexity

NutriPlan is meaningfully distinct from every other project in the CS50W curriculum and satisfies the complexity requirement in several ways, described in detail below.

### Why It Is Distinctive

NutriPlan is neither a social network nor an e-commerce site. It does not involve following other users, posting status updates, liking content, or any feed-based interaction model that would make it resemble Project 4 (Network). Nor does it involve purchasing, listings, bidding, or a shopping cart of any kind that would align it with Project 2 (Commerce).

Instead, NutriPlan occupies a completely different domain: personal nutrition and meal planning. The core loop of the application is: (1) a user authors their own recipes with ingredients and nutritional data, (2) they schedule those recipes across a 7-day weekly calendar by dragging and dropping recipe cards, and (3) the application automatically computes and displays aggregate nutritional totals (calories, protein, carbohydrates, fat) for each day. This is a productivity and health tool, not a social platform or marketplace.

The application also includes a recipe search and filtering system (filter by cuisine, dietary tag, or max prep time) powered by JavaScript fetch calls to a Django REST-style API endpoint, which returns JSON and updates the recipe list without a full page reload. This kind of dynamic, API-driven interface is a step beyond the project requirements and demonstrates a real-world single-page-app pattern inside a traditional Django project.

### Why It Is Complex

The complexity of NutriPlan emerges from several dimensions working together:

**Database design.** The application has five Django models: `Recipe`, `Ingredient`, `RecipeIngredient` (a many-to-many through table that stores per-ingredient quantity and unit), `DietaryTag`, and `MealPlanEntry`. The `MealPlanEntry` model links a user, a recipe, a specific date, and a meal slot (Breakfast, Lunch, Dinner, Snack). Getting these relationships right — especially the nutritional roll-up queries that aggregate across `RecipeIngredient` rows joined to `Ingredient` nutritional data — required careful use of Django's ORM `annotate` and `aggregate` functions.

**JavaScript drag-and-drop.** The weekly planner view is implemented as a calendar grid rendered server-side and then enhanced on the client with the HTML5 Drag and Drop API. Recipe cards in the sidebar are draggable. Calendar day-slot cells are drop targets. When a drop occurs, a `fetch` POST request is sent to `/api/mealplan/add/` with the recipe ID, date, and meal slot. The calendar cell is updated optimistically and the daily nutritional totals are recalculated in the browser without a page reload.

**Nutritional summary panel.** Each day column in the planner has a live-updating nutrition bar that shows calorie progress toward a configurable daily goal (stored in the user's profile). When a recipe is added or removed from a day slot, JavaScript recalculates the total and animates the progress bar. This required careful coordination between server-rendered initial state and client-side delta updates.

**Mobile responsiveness.** The planner calendar collapses from a 7-column grid to a vertically stacked, day-by-day accordion on small screens. This was achieved with CSS Grid and media queries, and the drag-and-drop is supplemented with tap-to-assign on touch devices using JavaScript `touchstart`/`touchend` events.

**User authentication & data isolation.** Every model that stores user data (recipes, meal plan entries, profile settings) is scoped to the authenticated user via a `ForeignKey` to `User`. The API endpoints enforce this with `@login_required` and by filtering all querysets to `request.user`, so one user can never read or modify another's data.

Taken together, these features — multi-table relational design, a drag-and-drop JavaScript interface, async API communication, live nutritional computation, and mobile-first layout — make NutriPlan substantially more complex than any individual project in the course.

---

## File Structure

```
capstone/
├── README.md
├── requirements.txt
├── manage.py
├── capstone/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── nutriplan/
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── forms.py
    ├── admin.py
    ├── templates/
    │   └── nutriplan/
    │       ├── layout.html
    │       ├── index.html
    │       ├── recipes.html
    │       ├── recipe_detail.html
    │       ├── recipe_form.html
    │       ├── planner.html
    │       ├── login.html
    │       └── register.html
    └── static/
        └── nutriplan/
            ├── styles.css
            └── planner.js
```

### File Descriptions

**`nutriplan/models.py`**
Defines five models:
- `DietaryTag` — a simple label (e.g. "Vegan", "Gluten-Free") that can be attached to recipes.
- `Ingredient` — a named ingredient with per-100 g nutritional values (calories, protein, carbs, fat).
- `Recipe` — a user-authored recipe with title, description, cuisine, prep time, servings, image, and many-to-many tags.
- `RecipeIngredient` — through-table connecting `Recipe` and `Ingredient`, storing quantity and unit so that nutritional totals per serving can be calculated.
- `MealPlanEntry` — records a (user, recipe, date, meal_slot) tuple to populate the weekly planner.

**`nutriplan/views.py`**
Contains all view functions:
- Standard Django views for the landing page, recipe list, recipe detail, recipe create/edit/delete, user registration, login, and logout.
- API views (`/api/recipes/`, `/api/mealplan/add/`, `/api/mealplan/remove/`) that return JSON and are called by the JavaScript front-end.
- A `planner` view that builds the 7-day calendar context (current week's entries grouped by date and meal slot) and passes it to the template.

**`nutriplan/urls.py`**
Maps all URL patterns for the `nutriplan` app, including the API sub-paths under `/api/`.

**`nutriplan/forms.py`**
Django `ModelForm` subclasses for `Recipe` creation/editing and user registration. Uses `django-crispy-forms` with the Bootstrap 5 template pack for styled form rendering.

**`nutriplan/admin.py`**
Registers all models with the Django admin site, with inline support for `RecipeIngredient` within the `Recipe` admin page.

**`nutriplan/templates/nutriplan/layout.html`**
Base template that loads Bootstrap 5 from CDN, defines the navigation bar (with dynamic login/logout links), and provides `{% block content %}` and `{% block scripts %}` blocks.

**`nutriplan/templates/nutriplan/planner.html`**
The most complex template. Renders a 7-column CSS Grid calendar for the current week. Each cell is a drop target. The sidebar lists the user's recipes as draggable cards. Includes `{% block scripts %}` to load `planner.js`.

**`nutriplan/templates/nutriplan/recipes.html`**
Recipe library view. Includes filter controls (cuisine dropdown, dietary tag checkboxes, max prep-time slider) that trigger JavaScript fetch calls to `/api/recipes/` and re-render the recipe card list in place.

**`nutriplan/static/nutriplan/planner.js`**
All client-side logic:
- Initializes HTML5 drag-and-drop on recipe cards and calendar cells.
- Handles `dragstart`, `dragover`, `drop`, and `dragleave` events.
- On drop, sends a `fetch` POST to `/api/mealplan/add/` and, on success, injects a new recipe chip into the calendar cell and updates the day's nutrition bar.
- Provides a `removeEntry(id)` function wired to delete buttons on each chip, calling `/api/mealplan/remove/`.
- Recalculates daily nutritional totals on every add/remove using data attributes stored on each chip.
- On mobile touch devices, replaces drag-and-drop with a two-step tap-to-select / tap-to-place interaction.

**`nutriplan/static/nutriplan/styles.css`**
Custom styles layered on top of Bootstrap:
- CSS Grid layout for the 7-column planner.
- Responsive media queries that collapse the grid to a stacked accordion on screens narrower than 768 px.
- Nutritional progress bar styles and color thresholds (green → amber → red as calorie goal is approached).
- Drag-over highlight state for calendar drop zones.

---

## How to Run

1. **Clone the repository:**
   ```bash
   git clone https://github.com/me50/USERNAME.git
   cd USERNAME
   git checkout web50/projects/2020/x/capstone
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser (optional, for Django admin):**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

7. **Open your browser** and navigate to `http://127.0.0.1:8000/`.

---

## Additional Notes

- Recipe images are stored in `MEDIA_ROOT` (defaults to a `media/` folder at the project root). Ensure `MEDIA_URL` and `MEDIA_ROOT` are configured in `settings.py` and that `django.views.static.serve` is used in `urls.py` during development.
- The application was developed and tested with Python 3.11 and Django 4.2.
- All API endpoints that mutate data (`/api/mealplan/add/`, `/api/mealplan/remove/`) are protected with Django's CSRF middleware; the JavaScript client reads the CSRF token from the `csrftoken` cookie and includes it in the `X-CSRFToken` request header.
- Nutritional data for ingredients is entered manually by the user when creating an ingredient. A future enhancement could integrate a third-party nutrition API to auto-populate these values.

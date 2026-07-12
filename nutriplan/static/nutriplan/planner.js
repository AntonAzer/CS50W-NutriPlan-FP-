'use strict';

// ─── State ────────────────────────────────────────────────────────────────────
let draggedRecipe = null;   // {id, title, calories, protein, carbs, fat}
let touchSelected = null;   // same shape, for mobile tap-to-place

// ─── Helpers ─────────────────────────────────────────────────────────────────

function getCookie(name) {
  const val = document.cookie.split(';')
    .map(c => c.trim())
    .find(c => c.startsWith(name + '='));
  return val ? decodeURIComponent(val.split('=')[1]) : null;
}

async function postJSON(url, data) {
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ─── Nutrition bar ────────────────────────────────────────────────────────────

function updateNutritionBar(dateStr, delta) {
  const el = document.querySelector(`.day-nutrition[data-date="${dateStr}"]`);
  if (!el) return;
  const goal = parseInt(el.dataset.goal, 10);
  let current = parseFloat(el.dataset.calories) + delta;
  if (current < 0) current = 0;
  el.dataset.calories = current;

  const bar = el.querySelector('.nutrition-bar');
  const display = el.querySelector('.cal-display');
  const pct = Math.min((current / goal) * 100, 100);
  bar.style.width = pct + '%';
  bar.classList.remove('warn', 'over');
  if (pct >= 100) bar.classList.add('over');
  else if (pct >= 80) bar.classList.add('warn');
  display.textContent = Math.round(current);
}

// ─── Entry chip DOM ───────────────────────────────────────────────────────────

function createEntryChip(entry) {
  const chip = document.createElement('div');
  chip.className = 'entry-chip';
  chip.dataset.entryId = entry.id;
  chip.dataset.calories = entry.nutrition.calories;
  chip.dataset.protein  = entry.nutrition.protein;
  chip.dataset.carbs    = entry.nutrition.carbs;
  chip.dataset.fat      = entry.nutrition.fat;
  chip.innerHTML = `
    <span class="entry-title">${entry.recipe_title}</span>
    <button class="remove-entry btn btn-link p-0 ms-1 text-danger" data-entry-id="${entry.id}" title="Remove">
      <i class="bi bi-x"></i>
    </button>`;
  return chip;
}

// ─── Remove entry ─────────────────────────────────────────────────────────────

async function removeEntry(entryId, chip) {
  try {
    const data = await postJSON('/api/mealplan/remove/', { entry_id: entryId });
    const dateStr = chip.closest('.drop-zone').dataset.date;
    updateNutritionBar(dateStr, -parseFloat(chip.dataset.calories));
    chip.remove();
  } catch (err) {
    console.error('Remove failed', err);
    alert('Could not remove entry. Please try again.');
  }
}

// ─── Add entry ────────────────────────────────────────────────────────────────

async function addEntry(zone, recipe) {
  const dateStr = zone.dataset.date;
  const mealSlot = zone.dataset.slot;
  try {
    const data = await postJSON('/api/mealplan/add/', {
      recipe_id: recipe.id,
      date: dateStr,
      meal_slot: mealSlot,
    });
    const chip = createEntryChip(data);
    zone.appendChild(chip);
    updateNutritionBar(dateStr, data.nutrition.calories);
  } catch (err) {
    console.error('Add failed', err);
    alert('Could not add recipe. Please try again.');
  }
}

// ─── Drag & Drop ─────────────────────────────────────────────────────────────

function initDragAndDrop() {
  // Recipe cards → drag source
  document.querySelectorAll('.draggable-recipe').forEach(card => {
    card.addEventListener('dragstart', e => {
      draggedRecipe = {
        id:       card.dataset.recipeId,
        title:    card.dataset.title,
        calories: parseFloat(card.dataset.calories),
        protein:  parseFloat(card.dataset.protein),
        carbs:    parseFloat(card.dataset.carbs),
        fat:      parseFloat(card.dataset.fat),
      };
      card.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'copy';
    });
    card.addEventListener('dragend', () => {
      card.classList.remove('dragging');
      draggedRecipe = null;
    });
  });

  // Drop zones
  document.querySelectorAll('.drop-zone').forEach(zone => {
    zone.addEventListener('dragover', e => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'copy';
      zone.classList.add('drag-over');
    });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', async e => {
      e.preventDefault();
      zone.classList.remove('drag-over');
      if (!draggedRecipe) return;
      await addEntry(zone, draggedRecipe);
    });
  });
}

// ─── Remove buttons (delegated) ───────────────────────────────────────────────

document.addEventListener('click', e => {
  const btn = e.target.closest('.remove-entry');
  if (!btn) return;
  const chip = btn.closest('.entry-chip');
  removeEntry(parseInt(btn.dataset.entryId, 10), chip);
});

// ─── Sidebar search ───────────────────────────────────────────────────────────

function initSidebarSearch() {
  const input = document.getElementById('sidebarSearch');
  if (!input) return;
  input.addEventListener('input', () => {
    const q = input.value.toLowerCase();
    document.querySelectorAll('.draggable-recipe').forEach(card => {
      const match = card.dataset.title.toLowerCase().includes(q);
      card.style.display = match ? '' : 'none';
    });
  });
}

// ─── Touch / mobile support ───────────────────────────────────────────────────

function initTouchSupport() {
  const banner = document.getElementById('mobileSelected');
  const nameEl  = document.getElementById('mobileSelectedName');
  const cancelBtn = document.getElementById('mobileCancelBtn');

  if (!banner) return;

  // Tap a recipe card to select it
  document.querySelectorAll('.draggable-recipe').forEach(card => {
    card.addEventListener('click', () => {
      touchSelected = {
        id:       card.dataset.recipeId,
        title:    card.dataset.title,
        calories: parseFloat(card.dataset.calories),
        protein:  parseFloat(card.dataset.protein),
        carbs:    parseFloat(card.dataset.carbs),
        fat:      parseFloat(card.dataset.fat),
      };
      nameEl.textContent = `Selected: ${touchSelected.title} — tap a meal slot to add`;
      banner.classList.remove('d-none');
    });
  });

  // Tap a drop zone to place
  document.querySelectorAll('.drop-zone').forEach(zone => {
    zone.addEventListener('click', async () => {
      if (!touchSelected) return;
      await addEntry(zone, touchSelected);
      touchSelected = null;
      banner.classList.add('d-none');
    });
  });

  cancelBtn.addEventListener('click', () => {
    touchSelected = null;
    banner.classList.add('d-none');
  });
}

// ─── Init ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  initDragAndDrop();
  initSidebarSearch();
  initTouchSupport();

  // Set initial bar colours
  document.querySelectorAll('.day-nutrition').forEach(el => {
    const goal = parseInt(el.dataset.goal, 10);
    const cal  = parseFloat(el.dataset.calories);
    const pct  = (cal / goal) * 100;
    const bar  = el.querySelector('.nutrition-bar');
    if (pct >= 100) bar.classList.add('over');
    else if (pct >= 80) bar.classList.add('warn');
  });
});

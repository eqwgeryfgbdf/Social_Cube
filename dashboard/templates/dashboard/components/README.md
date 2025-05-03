# Dashboard Layout Components

This directory contains reusable layout components for consistent styling across the application.

## Available Components

### 1. Card Component

**File:** `card.html`

**Description:** A standardized card container with consistent styling for all card-like elements in the UI.

**Usage:**
```html
{% include "dashboard/components/card.html" with title="Card Title" %}
  Your card content here
{% endinclude %}
```

**Parameters:**
- `title`: The title of the card (required)
- `no_padding`: Boolean to remove padding (default: false)
- `no_margin`: Boolean to remove margin (default: false)
- `header_actions`: HTML content for the header right side (optional)

### 2. Form Group Component

**File:** `form_group.html`

**Description:** A standardized container for form controls with consistent spacing and alignment.

**Usage:**
```html
{% include "dashboard/components/form_group.html" with layout="horizontal" %}
  <input type="text" placeholder="Input field">
  <button>Submit</button>
{% endinclude %}
```

**Parameters:**
- `layout`: "horizontal" or "vertical" (default: "vertical")
- `spacing`: spacing between items (default: 4 for vertical, 2 for horizontal)

### 3. Scrollable Content Component

**File:** `scrollable_content.html`

**Description:** A standardized scrollable content area for lists, logs, etc.

**Usage:**
```html
{% include "dashboard/components/scrollable_content.html" with height="64" id="log-container" %}
  <div>Scrollable content item 1</div>
  <div>Scrollable content item 2</div>
{% endinclude %}
```

**Parameters:**
- `height`: The height in Tailwind units (default: 64 = 16rem)
- `id`: The HTML id of the container (optional)

### 4. Page Container Component

**File:** `page_container.html`

**Description:** A standardized page container for consistent layout and spacing.

**Usage:**
```html
{% include "dashboard/components/page_container.html" with title="Dashboard" %}
  Your page content here
{% endinclude %}
```

**Parameters:**
- `title`: The title of the page (optional)

## Standardized Tailwind Classes

For consistency across the application, use these standardized Tailwind classes:

- **Page container:** `flex-1 overflow-y-auto px-4 py-6 sm:px-6 lg:px-8`
- **Card container:** `bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6`
- **Section header:** `text-xl font-semibold mb-4`
- **Form groups:** 
  - Vertical: `space-y-4`
  - Horizontal: `flex flex-wrap items-center gap-2`
- **Scrollable content:** `h-[height] overflow-y-auto rounded border dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-4`

## Example Implementation

```html
{% extends "dashboard/new_base.html" %}
{% load static %}

{% block content %}
{% include "dashboard/components/page_container.html" with title="Analytics Dashboard" %}
  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
    {% include "dashboard/components/card.html" with title="Recent Activity" %}
      {% include "dashboard/components/scrollable_content.html" with height="64" id="activity-log" %}
        <div>Activity item 1</div>
        <div>Activity item 2</div>
      {% endinclude %}
    {% endinclude %}
  </div>
{% endinclude %}
{% endblock %}
```
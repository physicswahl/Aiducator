# Game Page Template Documentation

The `gamepage.html` template provides a standardized base template for all AI game steps with consistent styling, navigation, and functionality.

## Features

### 1. Fixed Navigation
- **Fixed Navbar**: Navbar stays at the top when scrolling
- **Fixed Footer**: Navigation footer stays at the bottom when scrolling
- **Responsive Layout**: Both navbar and footer adjust properly on all screen sizes

### 2. Fixed Instructions Button
- Positioned on the left side of the screen
- Vertical text orientation
- Opens an offcanvas panel with step instructions
- Always accessible without scrolling

### 3. Consistent Card Layout
- Gradient header with game title and team matchup
- Clean card-based design with shadows
- Responsive layout

### 4. Fixed Footer Navigation
- Positioned at the bottom of the page
- Uses the same color as the navbar (dynamically from database via `navbar_color`)
- Context-aware navigation buttons:
  - **Previous Step**: Available for all steps except step 1
  - **Submit Button**: For steps requiring teacher validation
  - **Next Step**: For navigation to next step when accessible
  - **Complete/Final**: For final steps

### 5. Common Styling
- Bootstrap-based responsive design
- Consistent color scheme
- Pre-defined classes for common elements
- Status message utilities

## How to Use

### Basic Template Structure

```django
{% extends 'overlap/gamepage.html' %}
{% load static %}

{% block extra_step_css %}
    /* Step-specific CSS goes here */
{% endblock %}

{% block step_content %}
    <!-- Your step-specific content goes here -->
{% endblock %}

{% block step_scripts %}
    <!-- Step-specific JavaScript goes here -->
{% endblock %}
```

### Required Context Variables

The template expects these context variables to be provided by the view:

```python
context = {
    'matchup': matchup_object,
    'step_name': 'Step 1',  # or 'Step 2', etc.
    'current_step': 1,
    'total_steps': 5,
    'instructions': instruction_list,  # List of instruction objects
    
    # Navigation variables
    'previous_step_url': reverse('overlap:step1', args=[matchup.id]),
    'next_step_url': reverse('overlap:step3', args=[matchup.id]),
    'has_next_step': True,
    'next_step_accessible': True,
    
    # Submit functionality (for steps that require submission)
    'show_submit_button': True,  # If this step has a submit action
    'can_submit': True,  # If user can currently submit
    'submit_button_text': 'Submit for Teacher Validation',
    'submit_disabled_text': 'Complete requirements to submit',
    
    # Final step
    'completion_url': reverse('overlap:complete_step', args=[matchup.id]),
}
```

### Custom Navigation

If you need custom navigation buttons, override the `navigation_buttons` block:

```django
{% block navigation_buttons %}
    <a href="{% url 'overlap:step3' matchup.id %}" class="btn btn-outline-light">
        <i class="fas fa-arrow-left me-1"></i> Previous Step
    </a>
    
    <button type="button" class="btn btn-light" onclick="submitStep()">
        Submit for Teacher Validation
    </button>
{% endblock %}
```

### Submit Functionality

For steps that require submission, override the `submit_function` block:

```django
{% block submit_function %}
    // Your validation logic here
    if (!isValid) {
        showMessage('Please complete all fields.', 'warning');
        return;
    }
    
    // Confirm and submit
    if (confirm('Submit your work?')) {
        document.getElementById('myForm').submit();
    }
{% endblock %}
```

### Available CSS Classes

#### Status Messages
- `.status-success` - Green success message
- `.status-warning` - Yellow warning message  
- `.status-info` - Blue info message

#### Layout Sections
- `.config-section` - Gray background section for configuration
- `.canvas-container` - Centered container for canvas elements
- `.display-section` - Blue-bordered display area
- `.display-value` - Large display value
- `.display-label` - Small label under display value

#### Instructions
- `.instruction-step` - Individual instruction container
- `.instruction-content` - Content area within instruction

### Utility Functions

The template provides these JavaScript utility functions:

```javascript
// Show a message at the top of the card
showMessage(message, type);  // type: 'success', 'warning', 'error', 'info'
```

## Migration Guide

To convert existing step templates:

1. **Change the extends directive:**
   ```django
   <!-- From -->
   {% extends 'syllabus/base.html' %}
   
   <!-- To -->
   {% extends 'overlap/gamepage.html' %}
   ```

2. **Move step-specific CSS:**
   ```django
   {% block extra_step_css %}
       /* Move your step-specific styles here */
   {% endblock %}
   ```

3. **Wrap content in step_content block:**
   ```django
   {% block step_content %}
       <!-- Move your main content here -->
   {% endblock %}
   ```

4. **Remove duplicate navigation:**
   - Remove the old step-navigation div
   - Remove the instructions button and offcanvas
   - The base template handles these automatically

5. **Move JavaScript:**
   ```django
   {% block step_scripts %}
       <!-- Move your JavaScript here -->
   {% endblock %}
   ```

## Example Implementation

See `step1_new.html` and `step4_new.html` for complete examples of how to implement different types of steps using this base template.

## Benefits

1. **Consistency** - All steps have the same look and feel
2. **Maintainability** - Common features are centralized
3. **Responsive** - Fixed footer navigation works on all screen sizes
4. **Accessibility** - Consistent keyboard navigation and screen reader support
5. **Extensibility** - Easy to add new common features to all steps

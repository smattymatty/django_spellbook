---
name: Style System Enhancement
about: Propose enhancements to Django Spellbook's style system (colors, borders, spacing, flexbox, etc.)
title: "[STYLE] Component - Brief description"
labels: enhancement, styles
assignees: ''

---

## **Current Situation**

*Please provide a clear and concise description of what the problem is, or what the current state is if suggesting an enhancement.*

Example: Currently, colors are hard-coded in CSS files and cannot be customized through Django settings. This makes it difficult to maintain consistent theming across projects.

## **Proposed Solution(s)**

*Please describe the solution you'd like to see implemented or suggest ways to address the problem.*

Example: 
- Allow color schemes to be defined in Django settings as `SPELLBOOK_THEME`
- Generate CSS variables dynamically from Python configuration
- Support theme presets and custom color additions

## **Benefits**

*Please describe how this solution would benefit the project, its contributors, or its users.*

Example:
- Easier theme customization without modifying CSS files
- Consistent color management from a single source of truth
- Better maintainability and extensibility
- Runtime theme switching capabilities

## **Files to be Altered or Created (if known)**

*List any specific files or directories within the codebase that you believe will need to be modified to implement the proposed solution. If unsure, leave this blank.*

Example:
- `django_spellbook/templatetags/spellbook_tags.py` - Enhance spellbook_styles tag
- `django_spellbook/theme/` - New module for theme handling
- `django_spellbook/static/django_spellbook/css_modules/utilities/colors.css` - Update to use dynamic variables

## **Additional Context (Optional)**

*Add any other context, screenshots, or links about the issue here.*

### Style Component Being Enhanced
Please check which component(s) this enhancement targets:
- [ ] Colors & Theming
- [ ] Borders & Shadows
- [ ] Spacing (Padding/Margin)
- [ ] Flexbox & Grid
- [ ] Typography
- [ ] Transitions & Animations
- [ ] Layout & Sizing
- [ ] Effects & Filters
- [ ] Interactivity States
- [ ] Other: _____________

### Breaking Changes
Will this enhancement introduce breaking changes?
- [ ] Yes (requires major version bump)
- [ ] No (backwards compatible)

### Related Issues
Link any related issues or PRs: #
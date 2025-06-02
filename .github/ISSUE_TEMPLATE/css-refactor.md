## Task Description

This task involves refactoring a specific set of CSS utilities or component styles from the existing monolithic stylesheets into a new dedicated CSS module. This task is a sub-issue of the main "EPIC: CSS Architecture Refactor."

**Module Name for this Task:** [Specify the name of the module, e.g., Spacing Utilities, Typography Utilities, Alert Component Styles, Card Component Styles]
**Target File Path:** `django_spellbook/static/django_spellbook/css/[Specify path, e.g., utilities/spacing.css or components/card.css]`

## Scope & Affected Styles

* Identify and list all CSS classes, rules, or categories of styles that fall under this module and need to be migrated from their current locations (e.g., `utilities.css`, `styles.css`, or other existing files).
    * [Provide a detailed list or description of the styles to be moved. For example:
        * For Spacing Utilities: All `sb-p-*`, `sb-m-*`, `sb-gap-*` classes.
        * For Alert Component: All styles related to `.sb-alert`, `.sb-alert-info`, etc.
        * Be specific about the selectors and properties.]
* Note any CSS Custom Properties (variables) primarily used or defined by these styles. If these are theme-level variables, ensure they are sourced from `base/variables.css`. Module-specific variables can be defined locally if appropriate.

## Implementation Steps

1.  **Create Target File:**
    * Create the new CSS file at the specified `Target File Path`.
2.  **Migrate Styles:**
    * Carefully identify and cut all relevant CSS rules from their current locations.
    * Paste these rules into the new target file.
    * Organize the styles logically within the new file.
3.  **Verify Variable Usage:**
    * Ensure all CSS custom properties (variables) used are correctly defined (typically in `base/variables.css` for global theme variables) and will be available.
4.  **Update Main Import File:**
    * Add an `@import` statement for the new module file (e.g., `@import '../utilities/spacing.css';` or `@import '../components/alert.css';`) into the main `spellbook.css` file.
    * Ensure it is placed in a logical order relative to other imports (e.g., base styles first, then utilities, then components).
5.  **Testing (Visual Regression):**
    * Thoroughly test pages and components that utilize these styles to ensure no visual regressions.
    * Check different states (hover, focus, active) and responsive behaviors if applicable to the module.

## Acceptance Criteria

* All identified styles for this module are now exclusively located in the specified `Target File Path`.
* The old monolithic files no longer contain these specific styles (this may be progressive if multiple refactoring tasks are in parallel, but should be true upon completion of all related tasks).
* All functionalities and appearances related to these styles function as previously intended across the documentation site and example pages.
* The main `spellbook.css` file correctly imports the new module file.
* The implementation adheres to the project's CSS coding standards and uses CSS custom properties for themeable values where appropriate.

## Related Files & Documentation

* **Parent Epic:** [Link to the main "EPIC: CSS Architecture Refactor" issue]
* **Current Source CSS File(s) (for reference):** [e.g., `django_spellbook/static/django_spellbook/css/utilities.css`, `django_spellbook/static/django_spellbook/css/styles.css`]
* **Relevant Documentation:** [Link to any existing documentation pages that describe or showcase the styles being refactored, if applicable.]

## Testing Considerations

* Visually inspect all SpellBlocks, components, and example pages that use the affected styles.
* Test across different supported browsers.
* If these styles are theme-dependent, verify behavior with theme variables.
* Check for CSS specificity issues or conflicts that might arise from moving the styles.

---

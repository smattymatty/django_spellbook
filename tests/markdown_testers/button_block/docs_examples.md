# Button Block (`~ button ~`) Showcase

The `~ button ~` SpellBlock allows you to easily create styled HTML anchor (`<a>`) tags that look and behave like buttons. This is perfect for calls-to-action, navigation, and links that need to stand out. This guide demonstrates its parameters and common use cases for the link-focused button.

## Basic Usage

To create a basic button, you provide an `href` and the button's text content between the tags.

```
{~ button href="/getting-started" ~}
Get Started
{~~}
```

{~ button href="/getting-started" ~}
Get Started
{~~}

## Parameters Showcase

The `~ button ~` block offers several parameters for customization:

### `href` (Required)

This defines the URL the button links to. If omitted, it defaults to `"#"` but a warning will be logged.

```
{~ button href="/features" ~}
Learn About Features
{~~}
```
{~ button href="/features" ~}
Learn About Features
{~~}

```
{~ button ~}
Button with Default Href
{~~}
```
{~ button ~}
Button with Default Href
{~~}

### `type` (Visual Style)

Controls the button's appearance. Corresponds to predefined CSS classes (e.g., `sb-btn-primary`).
Default: `default`.
Supported types (based on your CSS): `default`, `primary`, `secondary`, `success`, `warning`, `danger`, `info`, `accent`, `black`, `white`.

**Primary Button:**
```
{~ button href="/submit" type="primary" ~}
Submit Action
{~~}
```
{~ button href="/submit" type="primary" ~}
Submit Action
{~~}

**Secondary Button:**
```
{~ button href="/details" type="secondary" ~}
View Details
{~~}
```
{~ button href="/details" type="secondary" ~}
View Details
{~~}

**Success Button:**
```
{~ button href="/checkout" type="success" ~}
Confirm Purchase
{~~}
```
{~ button href="/checkout" type="success" ~}
Confirm Purchase
{~~}

*(You can add more examples for `danger`, `warning`, `info`, `accent`, etc. as needed)*

### `size`

Adjusts the button's size (padding, font-size). Corresponds to CSS classes (e.g., `sb-btn-sm`).
Default: `md`. Supported: `sm`, `md`, `lg`.

**Small Button:**
```
{~ button href="/small-action" type="primary" size="sm" ~}
Small Primary
{~~}
```
{~ button href="/small-action" type="primary" size="sm" ~}
Small Primary
{~~}

**Medium Button (Default Size):**
```
{~ button href="/medium-action" type="secondary" size="md" ~}
Medium Secondary
{~~}
```
{~ button href="/medium-action" type="secondary" size="md" ~}
Medium Secondary
{~~}

**Large Button:**
```
{~ button href="/large-action" type="success" size="lg" ~}
Large Success
{~~}
```
{~ button href="/large-action" type="success" size="lg" ~}
Large Success
{~~}

### `target`

Standard HTML `target` attribute for links (e.g., `_blank` to open in a new tab).

```
{~ button href="https://example.com" target="_blank" type="info" ~}
Open External Link
{~~}
```
{~ button href="https://example.com" target="_blank" type="info" ~}
Open External Link
{~~}

### `disabled`

Renders the button in a disabled state. The `href` will point to `"#"` and ARIA attributes for disabled state will be added.
Default: `false`. Set to `true` to disable.

```
{~ button href="/secret-area" type="error" disabled="true" ~}
Access Restricted
{~~}
```

{~ button href="/secret-area" type="error" disabled="true" ~}
Access Restricted
{~~}

### `icon_left` and `icon_right`

Adds an icon to the left or right of the button text. You provide the CSS class for the icon.

**Icon Left:**
```
{~ button href="/download" type="primary" icon_left="sb-icon-download" ~}
Download File
{~~}
```
{~ button href="/download" type="primary" icon_left="sb-icon-download" ~}
Download File
{~~}

**Icon Right:**
```
{~ button href="/next" type="default" icon_right="sb-icon-arrow-right" ~}
Next Step
{~~}
```
{~ button href="/next" type="default" icon_right="sb-icon-arrow-right" ~}
Next Step
{~~}

**Both Icons:**
```
{~ button href="/settings" type="secondary" icon_left="sb-icon-settings" icon_right="sb-icon-edit" ~}
Manage Settings
{~~}
```
{~ button href="/settings" type="secondary" icon_left="sb-icon-settings" icon_right="sb-icon-edit" ~}
Manage Settings
{~~}

### `class` and `id`

Apply custom CSS classes or an HTML `id` for additional styling or JavaScript targeting.

```
{~ button href="/custom" class="my-special-button analytics-trigger" id="ctaButtonHomePage" type="accent" ~}
Special Offer
{~~}
```
{~ button href="/custom" class="my-special-button analytics-trigger" id="ctaButtonHomePage" type="accent" ~}
Special Offer
{~~}

## Content Formatting within Buttons

The text inside the button tags is processed as Markdown.

```
{~ button href="/formatted-content" type="primary" size="lg" ~}
Click **Here** for *Amazing* `Offers`!
{~~}
```
{~ button href="/formatted-content" type="primary" size="lg" ~}
Click **Here** for *Amazing* `Offers`!
{~~}

{~ alert type="warning" title="Note on Inner Content" ~}
Currently, simple text content like "More Info" inside a button might get wrapped in `<p>` tags by the Markdown processor (e.g., `<span><p>More Info</p></span>`). This is a known issue related to how inner block content is processed and ideally should result in plain inline text for button labels.
{~~}

## Combined Example

A button using multiple parameters:

```
{~ button
    href="/user/profile"
    type="info"
    size="lg"
    target="_blank"
    icon_left="sb-icon-user"
    class="user-profile-button"
    id="userProfileBtn"
~}
View My Profile
{~~}
```
{~ button
    href="/user/profile"
    type="info"
    size="lg"
    target="_blank"
    icon_left="sb-icon-user"
    class="user-profile-button"
    id="userProfileBtn"
~}
View My Profile
{~~}

## Use Cases

* **Primary Calls to Action:** Guide users to the most important actions (e.g., "Sign Up", "Buy Now").
* **Secondary Actions:** Offer alternative, less critical actions (e.g., "Learn More", "View Details").
* **Navigation:** Use link-styled buttons for subtle navigation items that still need a button's click area.
* **Downloads & External Links:** Clearly indicate actions like downloading files or navigating to external sites, often with icons.

---

{~ practice difficulty="Beginner" timeframe="15-20 minutes" impact="Medium" focus="UI Elements" ~}
### Button Practice Challenge

Create the following buttons:

1. A large, `primary` button that says "Register Today" and links to `/register`.
2. A small, `secondary` button that says "Read Documentation", opens in a new tab, and has a book icon on the left (e.g., `icon_left="sb-icon-book"`).
3. A `danger` button with default size that says "Delete Account" and has a warning icon on the right (e.g., `icon_right="sb-icon-warning"`). Make this button appear `disabled`.
4. A default styled button with your name and a custom class `my-name-button`.
{~~}
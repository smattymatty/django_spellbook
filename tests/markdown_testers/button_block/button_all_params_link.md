# Button All Parameters Link Test

This test case demonstrates a button with many parameters set, including type, size, icons, target, disabled state, custom class, and ID.
The button text is provided as inner content.

{~ button
    href="/all-features-showcase"
    type="success"
    size="lg"
    target="_blank"
    disabled="false"
    icon_left="sb-icon-rocket"
    icon_right="sb-icon-external-link"
    class="extra-styling demo-button"
    id="allParamsButton1"
~}
Explore All Features!
{~~}

And a disabled example with all parameters:

{~ button
    href="/another-link-never-reached"
    type="danger"
    size="sm"
    target="_top"
    disabled="true"
    icon_left="sb-icon-lock"
    icon_right="sb-icon-warning"
    class="locked-feature old-style"
    id="allParamsButtonDisabled"
~}
Feature Locked
{~~}
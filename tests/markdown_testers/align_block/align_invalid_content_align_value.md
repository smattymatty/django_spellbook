---
title: Align Invalid Content Align Value Test
---
{~ align content_align="upside-down" ~}
This block has an **invalid 'content_align' value** (`upside-down`).
The content alignment should default to `center` (or your defined default).
A warning should be logged by the `AlignBlock` Python class.
{~~}
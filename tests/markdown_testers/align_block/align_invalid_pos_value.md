---
title: Align Invalid Pos Value Test
---
{~ align pos="super-duper-left" width="80%" ~}
This block has an **invalid 'pos' value** (`super-duper-left`).
It should default to `pos="center"` (or your defined default).
The block should be 80% wide and centered.
A warning should be logged by the `AlignBlock` Python class.
{~~}
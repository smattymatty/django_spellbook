---
title: Align Height 200px Test
---
{~ align height="200px" ~}
This block should have a **height of 200px**.
The `AlignBlock`'s Python code currently expects "auto" or "NN%" for height. If "200px" is passed as a string, the template will need to handle it directly.
This tests that the string value is passed through.
Content should be vertically centered within this height if your CSS/template supports it.
{~~}
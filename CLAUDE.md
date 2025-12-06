# Claude Code Notes

## Common Mistakes I Make

### 1. **Not Reading Files Before Analysis**
I frequently jump into analysis or search tasks without first reading the actual file contents. This leads to:
- Making assumptions about code structure
- Missing context that would be obvious from reading
- Wasting time with speculative searches when a simple file read would answer the question

**Example from this investigation:** I ran multiple greps and bash commands before actually reading any core source files. Should have started with reading key files like the main module files.

### 2. **Over-relying on grep/search instead of just reading**
When asked to understand something, I tend to:
- Run multiple grep patterns
- Search for keywords
- Look for patterns

When I should just:
- Read the relevant files directly
- Understand the code structure first
- Then search if needed

### 3. **Forgetting to check CHANGELOG.md**
Changelogs often contain valuable context about:
- Recent changes
- Known issues
- Project direction
- Version history

I should check the CHANGELOG earlier in investigations.

### 4. **Not using TodoWrite for multi-step investigations**
For complex tasks like code investigations, I should:
- Create a todo list at the start
- Track what I've investigated
- Mark items complete as I go
- Ensure I don't miss important areas

## Best Practices for Working with This Codebase

### Project Structure
```
django_spellbook/
├── markdown/           # Core markdown parsing engine
├── spellblocks.py     # Reusable content components
├── theme/             # Theme system
├── management/        # Django commands (spellbook_md)
└── templatetags/      # Django template tags
```

### Key Entry Points
- `parsers.py` - Main public API (`render_spellbook_markdown_to_html`)
- `spellblocks.py` - SpellBlock registry and built-in blocks
- `management/commands/spellbook_md.py` - Batch processing command

### Testing
- Run tests with: `python manage.py test`
- 674 tests as of 12/06/2025
- Tests use `TESTING=True` flag to skip INSTALLED_APPS validation

## Tips for Future Claude Sessions

1. **Always read the README and CHANGELOG first** - Don't skip this step
2. **Read actual source files** - Don't rely solely on grep
3. **Check for uncommitted changes** - Use `git status` early
4. **Use TodoWrite for investigations** - Track progress systematically
5. **Look for test files** - They often document expected behavior and known issues
6. **Check for TODO/FIXME comments** - They highlight known issues and future work
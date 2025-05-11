# **First Rough Draft of Proposed Models that this app can utilize:**

Here are my ideas.
I hope the comments help. I will start with the imports:

```python
# django_spellbook/edu/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
# Using Django_taggit would be a good idea for flexible tagging
# https://django-taggit.readthedocs.io/en/latest/getting_started.html
from django_taggit.managers import TaggableManager
# You would be able to extend these models, and update the settings.py
# -- Default models are in django_spellbook.edu.models --
# SPELLBOOK_EDU_QUESTION_MODEL = 'django_spellbook.edu.models.SpellbookQuestion'
# SPELLBOOK_EDU_ANSWER_MODEL = 'django_spellbook.edu.models.SpellbookAnswer'
# These helper functions retrieve the models from the settings.py
from django_spellbook.edu.conf import get_question_model, get_answer_model

import uuid
```

Like the comments mention, you, or any app creator will be able to extend from this library.

```python
# settings.py
INSTALLED_APPS = [
...
"django_spellbook.edu"
...
]
```

In order to use a parser in your own views logic, import from `django_spellbook.parsers:`

```python
from django_spellbook.parsers import render_spellbook_markdown_to_html

def my_view(request)
    unparsed_content = whatever_logic_you_want()
    parsed_content = render_spellbook_markdown_to_html(unparsed_content)

    context = {'any_name_to_access_rendered_html' : parsed_content }
    template = "my_template"
    return render(request, template, context)

```

Running that function, or the `python manage.py spellbook_md` command, would theoretically parse all {~ question ~} and {~ answer ~} spellblocks to populate the database with these models. This would allow for educators, or students of all backgrounds to easily contribute or consume lightweight educational content with a Q&A database managed easily within their markdown.

We would have to think carefully about how these models would link together, and work together.

Firstly, the `ContentSource` will be the base for each question/answer, tying them back to their source. Ideally, each Question/Answer id should be unique within their content source.

```python
class ContentSource(models.Model):
    """
    Represents a distinct source of Spellbook educational content,
    such as a specific markdown file, a lesson within a course,
    or a user's collection of notes.

    Question/Answer IDs from SpellBlocks need to be unique within a ContentSource.
    """
    # The primary key for the database record
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # An identifier that spellbook parsing can consistently generate or that the host app can provide.
    # This could be a relative file path, a slugified lesson title, or a user ID + document ID.
    source_identifier = models.CharField(
        max_length=1024,
        unique=True, # Each source_identifier string should be unique globally
        db_index=True,
        help_text=_(
            """A unique string identifying the origin of this content batch 
            (e.g., 'course/lesson1/notes.md' or 'user123-documentXYZ')."""
            ),
        # When the app creator wants to add their own questions/answers outside of spellbook markdown parsing,
        blank=False,
        # They must give this a unique source_identifier. This cannot be empty or null.
        Null=False,
    )
    # Potentially, a canonical URL for this source if it's web-accessible
    # Running a spellbook_md, which generates many urls, will populate this automatically.
    # If the app creator has a custom way to parse markdown and generate urls, they can populate this themselves.
    canonical_url = models.URLField(
        max_length=2048,
        blank=True,
        null=True,
        help_text=_("Optional canonical URL where this content source is publicly accessible.")
    )
    # Timestamps for the source itself
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # When this source's content was last changed

    # Optional: Link to a user if content is user-specific
    owner = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.source_identifier

    class Meta:
        verbose_name = _("Spellbook Content Source")
        verbose_name_plural = _("Spellbook Content Sources")
```

Now, for the AbstractSpellbookQuestion (Any question models within the app can extend off of this):

```python
class AbstractSpellbookQuestion(models.Model):
    """
    Abstract base model for a question defined by a SpellBlock.
    Includes fields common to all question types.
    If the app creator needs to add additional fields, they can extend this model.
    """
    QUESTION_TYPE_CHOICES = [
        ('standard', _('Standard')), # Defined via {~ question ... ~}
        ('true_false_statement', _('True/False Statement')), # Implicitly from {~ answer correct=... ~}
        # ('multiple_choice', _('Multiple Choice')), # Future
        # ('essay', _('Essay')), # Future?
    ]
    question_type = models.CharField(
        max_length=50,
        choices=QUESTION_TYPE_CHOICES,
        default='standard',
        help_text=_("The nature or format of the question.")
    )
    # id is the ID from the markdown, e.g., "duck-joke-1"
    id = models.CharField(
        _("SpellBlock ID"),
        max_length=255,
        db_index=True,
        help_text=_("ID defined in the markdown {~ question id=... ~} spell. Unique within its ContentSource.")
    )

    content_source = models.ForeignKey(
        ContentSource,
        on_delete=models.CASCADE, # If source is deleted, its questions are too
        related_name="questions",
        verbose_name=_("Content Source")
    )

    # The actual primary key for the database record
    db_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(
        _("Title"),
        max_length=512,
        blank=True,
        help_text=_("Title of the question (e.g., from header or 'title' param).")
    )
    body = models.TextField(
        _("Body/Text"),
        blank=True,
        help_text=_("The main text/content of the question.")
    )
    # Django-taggit for flexible tagging
    # https://django-autocomplete-light.readthedocs.io/en/master/taggit.html
    tags = TaggableManager(
        verbose_name=_("Tags"),
        blank=True
    )
    difficulty = models.CharField(
        _("Difficulty"),
        max_length=50,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        abstract = True
        # Uniqueness constraint: id must be unique FOR EACH content_source
        unique_together = [['content_source', 'id']]
        verbose_name = _("Abstract Spellbook Question")
        ordering = ['content_source', 'id']

    def __str__(self):
        return f"{self.content_source.source_identifier} - {self.title or self.spellblock_id}"
```

If the app creator does not need to extend extra fields, the `django_spellbook.edu` would prepare a base model to use as default:

```python
from django_spellbook.edu.conf import get_question_model_string, DEFAULT_QUESTION_MODEL
# Only define the concrete SpellbookQuestion if the setting points to it
if get_question_model_string() == DEFAULT_QUESTION_MODEL:
    class SpellbookQuestion(AbstractSpellbookQuestion):
        class Meta:
            verbose_name = _("Spellbook Question")
            verbose_name_plural = _("Spellbook Questions")
```

Now, the same pattern for `AbstractSpellbookAnswer`:

```python
class AbstractSpellbookAnswer(models.Model): # Removed BaseSpellbookContentModel inheritance
    """
    Abstract base model for an answer/choice linked to a SpellbookQuestion.
    The app creator can add their own fields by extending this model.
    """
    answer_pk = models.AutoField(primary_key=True) # Internal primary key

    id = models.CharField(
        _("Answer ID"),
        max_length=255,
        db_index=True,
        help_text=_("Unique ID defined in the markdown {~ answer id=... ~} spell. This is the primary link for answers.")
    )

    answer_text = models.TextField(_("Answer Text/Content"))
    is_correct = models.BooleanField(_("Is Correct Choice?"), default=False)
    explanation = models.TextField(_("Explanation"), blank=True, null=True)
    tags = TaggableManager(verbose_name=_("Answer Tags"), blank=True)
    display_order = models.PositiveIntegerField(_("Display Order"), default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_question(self) -> AbstractSpellbookQuestion:
        # find question by linked id 
        return self.question

    class Meta:
        abstract = True
        verbose_name = _("Abstract Spellbook Answer")
        unique_together = [['question', 'id']]
        ordering = ['question', 'display_order', 'answer_pk']

    def __str__(self):
        return f"Answer for Q '{self.question.spellblock_id}': {self.answer_text[:50]}..."
```

If the basic fields meet the app creators needs, they may use the base model for answers:

```python
from django_spellbook.edu.conf import get_answer_model_string, DEFAULT_ANSWER_MODEL
# Only define the concrete SpellbookAnswer if the setting points to it
if get_answer_model_string() == DEFAULT_ANSWER_MODEL:
    class SpellbookAnswer(AbstractSpellbookAnswer):
        """
        The default out-of-the-box answer model.
        To be imported and used if the app creator does not need to add additional fields.
        """
        class Meta:
            verbose_name = _("Spellbook Answer")
            verbose_name_plural = _("Spellbook Answers")
```

This is just a first draft, but the idea is to make sure these models are easily `importable` and `extendable`. I think the most important things are id, tags, and way to get back to the source. The whole architecture of this data can change in the next draft, but the core idea of extracting question/answer models unique to their content by ids, and then linking those models by ids (e.g 'duck-joke-1' would have a question and answer with same id, used to refer back to each-other by the same content source).

---

{~ alert type="info" ~}
Here is an alert, for fun.
{~~}

{~ card title="Card Title" footer="Card Footer" ~}
Notice how these are unstyled, but the HTML is still properly rendered.
{~~}

{~ practice ~}
That's because `% spellbook_styles %` is not included here. You would need to include it in your template head.
{~~}

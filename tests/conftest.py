# tests/conftest.py
import django
from django.conf import settings


def pytest_configure():
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'django_spellbook',
        ],
        MIDDLEWARE=[],
        ROOT_URLCONF='',
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'APP_DIRS': True,
        }],
        SECRET_KEY='test-key',
        SPELLBOOK_MD_PATH='/test/path',
        SPELLBOOK_CONTENT_APP='test_app',
    )
    django.setup()

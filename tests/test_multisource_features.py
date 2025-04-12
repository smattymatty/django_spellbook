from django.test import TestCase, override_settings
from django.core.management import call_command
from django.urls import reverse, resolve, clear_url_caches
from pathlib import Path
import tempfile
import shutil
import sys
import importlib

class MultiSourceIntegrationTest(TestCase):
    """Full integration test with real file processing and URL resolution"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.temp_dir = Path(tempfile.mkdtemp())
        
        # Add temporary directory to Python path
        sys.path.insert(0, str(cls.temp_dir))
        
        # Setup proper app structure
        cls.setup_applications()
        cls.create_sample_content()
        cls.create_root_urlconf()
        
        # Apply temporary settings
        cls.override = override_settings(
            ALLOWED_HOSTS=['testserver'],
            SPELLBOOK_MD_PATH=[
                str(cls.temp_dir / 'docs_content'),
                str(cls.temp_dir / 'blog_content')
            ],
            SPELLBOOK_MD_APP=['docs', 'blog'],
            INSTALLED_APPS=[
                'django.contrib.staticfiles',
                'django.contrib.contenttypes',
                'django.contrib.auth',
                'docs.apps.DocsConfig',
                'blog.apps.BlogConfig',
                'django_spellbook'
            ],
            TEMPLATES=[
                {
                    'BACKEND': 'django.template.backends.django.DjangoTemplates',
                    'APP_DIRS': True,
                    'OPTIONS': {
                        'context_processors': [
                            'django.template.context_processors.request',
                        ],
                    },
                },
            ],
            ROOT_URLCONF='test_urls'
        )
        cls.override.enable()
        
        # Generate the content
        call_command('spellbook_md')
        
        # Reload URLconf after generation
        clear_url_caches()
        importlib.reload(importlib.import_module('test_urls'))

    @classmethod
    def tearDownClass(cls):
        cls.override.disable()
        shutil.rmtree(cls.temp_dir)
        sys.path.remove(str(cls.temp_dir))
        super().tearDownClass()

    @classmethod
    def setup_applications(cls):
        """Create proper Django app structures"""
        # Create docs app
        docs_app = cls.temp_dir / 'docs'
        docs_app.mkdir()
        (docs_app / '__init__.py').touch()
        (docs_app / 'apps.py').write_text(
            "from django.apps import AppConfig\n"
            "class DocsConfig(AppConfig):\n"
            "    default_auto_field = 'django.db.models.BigAutoField'\n"
            "    name = 'docs'\n"
        )
        (docs_app / 'templates' / 'docs' / 'spellbook_md').mkdir(parents=True)

        # Create blog app
        blog_app = cls.temp_dir / 'blog'
        blog_app.mkdir()
        (blog_app / '__init__.py').touch()
        (blog_app / 'apps.py').write_text(
            "from django.apps import AppConfig\n"
            "class BlogConfig(AppConfig):\n"
            "    default_auto_field = 'django.db.models.BigAutoField'\n"
            "    name = 'blog'\n"
        )
        (blog_app / 'templates' / 'blog' / 'spellbook_md').mkdir(parents=True)

        # Create content directories
        (cls.temp_dir / 'docs_content').mkdir()
        (cls.temp_dir / 'blog_content').mkdir()

    @classmethod
    def create_root_urlconf(cls):
        """Create temporary root URL configuration"""
        urls_content = """from django.urls import include, path\nurlpatterns = [
            path('docs/', include('django_spellbook.urls_docs')),
            path('blog/', include('django_spellbook.urls_blog'))
        ]"""
        (cls.temp_dir / 'test_urls.py').write_text(urls_content)

    @classmethod
    def create_sample_content(cls):
        """Create test markdown files with frontmatter"""
        # Docs content
        (cls.temp_dir / 'docs_content' / 'intro.md').write_text(
            "---\ntitle: Documentation Intro\n---\n# Welcome to Docs\nThis is documentation."
        )
        
        # Blog content
        (cls.temp_dir / 'blog_content' / 'first-post.md').write_text(
            "---\ntitle: First Post\n---\n# Blog Begins\nThis is our first blog post."
        )

    def test_template_generation(self):
        """Test that markdown files are converted to proper templates"""
        docs_template = self.temp_dir / 'docs' / 'templates' / 'docs' / 'spellbook_md' / 'intro.html'
        self.assertTrue(docs_template.exists(), f"Docs template not found at {docs_template}")
        
        content = docs_template.read_text()
        self.assertIn("<h1>Welcome to Docs</h1>", content)
        self.assertIn("This is documentation.", content)

        blog_template = self.temp_dir / 'blog' / 'templates' / 'blog' / 'spellbook_md' / 'first-post.html'
        self.assertTrue(blog_template.exists(), f"Blog template not found at {blog_template}")
        content = blog_template.read_text()
        self.assertIn("<h1>Blog Begins</h1>", content)
        self.assertIn("first blog post", content)

    def test_url_configuration(self):
        """Test that URLs are properly configured"""
        # Test docs URL
        docs_url = reverse('docs:intro')
        self.assertEqual(docs_url, '/docs/intro/')
        
        # Test blog URL
        blog_url = reverse('blog:first-post')
        self.assertEqual(blog_url, '/blog/first-post/')

    def test_content_serving(self):
        """Test that generated content is accessible through views"""
        response = self.client.get('/docs/intro/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome to Docs")
        
        response = self.client.get('/blog/first-post/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Blog Begins")
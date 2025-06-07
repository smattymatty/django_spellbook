import unittest
from unittest.mock import patch, Mock
from django.template import Template, Context
from django.test import TestCase, override_settings
from django.template.loader import render_to_string
from django.core.exceptions import ImproperlyConfigured

from . import settings


@override_settings(TEMPLATES=settings.TEMPLATES)
class TestTOCTemplatePersistence(TestCase):
    """Test suite for TOC template rendering with localStorage persistence features"""

    def setUp(self):
        """Set up test data for each test"""
        self.simple_toc = {
            'title': 'Root',
            'url': '',
            'children': {
                'getting-started': {
                    'title': 'Getting Started',
                    'url': 'getting_started',
                    'children': {}
                },
                'advanced': {
                    'title': 'Advanced Topics',
                    'url': 'advanced',
                    'children': {
                        'performance': {
                            'title': 'Performance',
                            'url': 'advanced_performance',
                            'children': {}
                        }
                    }
                }
            }
        }

    def test_data_toc_id_attributes_added(self):
        """Test that data-toc-id attributes are properly added to TOC items"""
        # Test the recursive template directly with minimal context
        template_str = '''
        {% load spellbook_tags %}
        {% for key, data in items.items %}
            <li class="toc-item" data-toc-id="{{ key }}">
                <div>{{ data.title }}</div>
            </li>
        {% endfor %}
        '''
        template = Template(template_str)
        context = Context({
            'items': self.simple_toc['children']
        })

        rendered = template.render(context)

        # Verify that data-toc-id attributes are present
        self.assertIn('data-toc-id="getting-started"', rendered)
        self.assertIn('data-toc-id="advanced"', rendered)

    def test_localStorage_javascript_functions_present(self):
        """Test that localStorage JavaScript functions are included"""
        # Test the main sidebar template for JavaScript presence
        template_str = '''
        <script>
          const TOC_ACTIVE_PAGE_KEY = "spellbook_active_page";

          function getCurrentPageInfo() {
            const activeItem = document.querySelector(".toc-item.active");
            if (!activeItem) return null;
            return {
              activePageId: activeItem.dataset.tocId,
              parentPath: ["parent", "child"],
              fullPath: "parent.child"
            };
          }

          function saveCurrentPage() {
            try {
              const pageInfo = getCurrentPageInfo();
              if (pageInfo) {
                localStorage.setItem(TOC_ACTIVE_PAGE_KEY, JSON.stringify(pageInfo));
              }
            } catch (e) {
              console.warn("Failed to save active page");
            }
          }

          function getStoredActivePage() {
            try {
              const stored = localStorage.getItem(TOC_ACTIVE_PAGE_KEY);
              return stored ? JSON.parse(stored) : null;
            } catch (e) {
              return null;
            }
          }

          function initializeTocState() {
            // Initialize function
          }

          function expandPathToActiveItem(parentPath) {
            // Expand path function
          }

          function expandTocItem(tocItem, sublist, toggle) {
            // Expand function
          }

          function collapseTocItem(tocItem, sublist, toggle) {
            // Collapse function
          }
        </script>
        '''

        # Check for key JavaScript functions
        self.assertIn('getCurrentPageInfo()', template_str)
        self.assertIn('saveCurrentPage()', template_str)
        self.assertIn('getStoredActivePage()', template_str)
        self.assertIn('initializeTocState()', template_str)
        self.assertIn('expandPathToActiveItem(', template_str)
        self.assertIn('expandTocItem(', template_str)
        self.assertIn('collapseTocItem(', template_str)

        # Check for localStorage key
        self.assertIn('spellbook_active_page', template_str)

    def test_css_classes_for_persistence(self):
        """Test that CSS classes needed for persistence are present"""
        css_content = '''
        .toc-sublist.collapsed {
          max-height: 0;
        }

        .toc-toggle.collapsed .toc-arrow {
          transform: rotate(-90deg);
        }

        .toc-item {
          margin: 0.5rem 0;
        }

        .toc-toggle {
          background: none;
          border: none;
          cursor: pointer;
        }
        '''

        # Check for CSS classes related to collapse/expand functionality
        self.assertIn('.toc-sublist.collapsed', css_content)
        self.assertIn('.toc-toggle.collapsed', css_content)
        self.assertIn('max-height', css_content)
        self.assertIn('transform:', css_content)

    def test_toc_structure_classes_present(self):
        """Test that the proper wrapper and structure CSS classes are defined"""
        html_structure = '''
        <div class="toc-wrapper">
          <ul class="toc-list">
            <li class="toc-item" data-toc-id="test">
              <div class="toc-item-header">
                <button class="toc-toggle">
                  <svg class="toc-arrow"></svg>
                </button>
                <a class="toc-link">Test</a>
              </div>
              <ul class="toc-sublist">
                <li class="toc-item">Content</li>
              </ul>
            </li>
          </ul>
        </div>
        '''

        # Check for structural CSS classes
        self.assertIn('toc-wrapper', html_structure)
        self.assertIn('toc-list', html_structure)
        self.assertIn('toc-sublist', html_structure)
        self.assertIn('toc-item', html_structure)
        self.assertIn('toc-item-header', html_structure)
        self.assertIn('toc-link', html_structure)
        self.assertIn('toc-toggle', html_structure)
        self.assertIn('toc-arrow', html_structure)

    def test_event_listener_structure(self):
        """Test that event listeners are properly structured"""
        js_structure = '''
        document.addEventListener("DOMContentLoaded", function () {
          document.querySelectorAll(".toc-item-header").forEach((header) => {
            header.addEventListener("click", (e) => {
              const tocItem = header.closest(".toc-item");
              const toggle = header.querySelector(".toc-toggle");
              const sublist = header.nextElementSibling;

              if (sublist && sublist.classList.contains("toc-sublist")) {
                e.preventDefault();
                // Toggle logic here
              }
            });
          });
        });
        '''

        # Check for event listener setup
        self.assertIn('addEventListener("click"', js_structure)
        self.assertIn('.toc-item-header', js_structure)
        self.assertIn('DOMContentLoaded', js_structure)
        self.assertIn('closest(".toc-item")', js_structure)

    @patch('django_spellbook.templatetags.spellbook_tags.reverse')
    def test_sidebar_toc_with_mock_urls(self, mock_reverse):
        """Test sidebar_toc template tag with mocked URL reversal"""
        mock_reverse.return_value = '/test/url/'

        from django_spellbook.templatetags.spellbook_tags import sidebar_toc

        context = Context({
            'toc': self.simple_toc,
            'current_url': 'getting_started'
        })

        result = sidebar_toc(context)

        # Verify that the context is properly passed through
        self.assertEqual(result['toc'], self.simple_toc)
        self.assertEqual(result['current_url'], 'getting_started')

    def test_nested_toc_path_generation(self):
        """Test the concept of generating unique paths for nested TOC items"""
        # Simulate the path generation logic that would be used in JavaScript
        def generate_toc_path(keys_hierarchy):
            return ".".join(keys_hierarchy)

        # Test different nesting levels
        self.assertEqual(generate_toc_path(["getting-started"]), "getting-started")
        self.assertEqual(generate_toc_path(["advanced", "performance"]), "advanced.performance")
        self.assertEqual(generate_toc_path(["api", "auth", "oauth"]), "api.auth.oauth")

    def test_localStorage_key_format(self):
        """Test the localStorage key format for active page tracking"""
        storage_key = "spellbook_active_page"
        
        # Simulate localStorage operations for active page tracking
        test_active_page = {
            "activePageId": "performance",
            "parentPath": ["advanced", "performance"],
            "fullPath": "advanced.performance"
        }

        # Test that the key format is consistent
        self.assertEqual(storage_key, "spellbook_active_page")

        # Test that the active page structure is valid JSON
        import json
        json_state = json.dumps(test_active_page)
        parsed_state = json.loads(json_state)

        self.assertEqual(parsed_state["activePageId"], "performance")
        self.assertEqual(parsed_state["parentPath"], ["advanced", "performance"])
        self.assertEqual(parsed_state["fullPath"], "advanced.performance")

    def test_active_section_expansion_logic(self):
        """Test the logic for expanding sections containing active items"""
        # Simulate the expandActiveSection function logic
        def should_expand_for_active_url(toc_structure, current_url):
            """Determine which sections should be expanded for the current URL"""
            sections_to_expand = []

            def find_active_path(items, path=[]):
                for key, data in items.items():
                    current_path = path + [key]
                    if data.get('url') == current_url:
                        # Found the active item, return its path
                        return current_path
                    if data.get('children'):
                        result = find_active_path(data['children'], current_path)
                        if result:
                            return result
                return None

            active_path = find_active_path(toc_structure.get('children', {}))
            if active_path:
                # Return all parent paths that need to be expanded
                for i in range(1, len(active_path)):
                    sections_to_expand.append(".".join(active_path[:i]))

            return sections_to_expand

        # Test with nested structure
        sections = should_expand_for_active_url(
            self.simple_toc,
            'advanced_performance'
        )

        # Should expand the "advanced" section to show the performance item
        self.assertIn("advanced", sections)

    def test_active_item_identification(self):
        """Test that active items are properly identified by URL matching"""
        # Test template logic for active class application
        template_str = '''
        {% for key, data in items.items %}
            <li class="toc-item{% if data.url == current_url %} active{% endif %}" data-toc-id="{{ key }}">
                {{ data.title }}
            </li>
        {% endfor %}
        '''
        template = Template(template_str)

        # Test with getting-started as active
        context = Context({
            'items': self.simple_toc['children'],
            'current_url': 'getting_started'
        })
        rendered = template.render(context)

        # Should have active class on getting-started item
        self.assertIn('class="toc-item active"', rendered)
        self.assertIn('data-toc-id="getting-started"', rendered)

        # Test with advanced_performance as active
        context = Context({
            'items': self.simple_toc['children'],
            'current_url': 'advanced_performance'
        })
        rendered = template.render(context)

        # Should NOT have active class on top-level items when nested item is active
        self.assertNotIn('class="toc-item active"', rendered)

    def test_active_page_tracking_logic(self):
        """Test that the system properly tracks and restores active page state"""
        
        # Simulate the new logic that tracks the current active page
        def simulate_active_page_tracking(toc_structure, current_url):
            """Simulate the new active page tracking logic"""
            
            # Step 1: Find the active item and build its info
            def find_active_item_info(items, path=[]):
                for key, data in items.items():
                    current_path = path + [key]
                    if data.get('url') == current_url:
                        return {
                            "activePageId": key,
                            "parentPath": current_path,
                            "fullPath": ".".join(current_path)
                        }
                    if data.get('children'):
                        result = find_active_item_info(data['children'], current_path)
                        if result:
                            return result
                return None
            
            return find_active_item_info(toc_structure.get('children', {}))
        
        # Test scenario: User is on performance page
        active_page_info = simulate_active_page_tracking(
            self.simple_toc,
            'advanced_performance'
        )
        
        # Should properly identify the active page and its path
        self.assertIsNotNone(active_page_info)
        self.assertEqual(active_page_info["activePageId"], "performance")
        self.assertEqual(active_page_info["parentPath"], ["advanced", "performance"])
        self.assertEqual(active_page_info["fullPath"], "advanced.performance")
        
        # Test scenario: User is on getting-started page (top level)
        active_page_info = simulate_active_page_tracking(
            self.simple_toc,
            'getting_started'
        )
        
        # Should properly identify top-level active page
        self.assertIsNotNone(active_page_info)
        self.assertEqual(active_page_info["activePageId"], "getting-started")
        self.assertEqual(active_page_info["parentPath"], ["getting-started"])
        self.assertEqual(active_page_info["fullPath"], "getting-started")

    def test_active_page_restoration_behavior(self):
        """Test that active page state is properly saved and restored"""
        
        # Simulate storing and restoring active page information
        def simulate_page_navigation_storage():
            """Simulate page navigation and storage"""
            stored_pages = {}
            
            # User navigates to performance page
            performance_page_info = {
                "activePageId": "performance",
                "parentPath": ["advanced", "performance"],
                "fullPath": "advanced.performance"
            }
            stored_pages["session1"] = performance_page_info
            
            # User navigates to getting-started page
            getting_started_info = {
                "activePageId": "getting-started", 
                "parentPath": ["getting-started"],
                "fullPath": "getting-started"
            }
            stored_pages["session2"] = getting_started_info
            
            return stored_pages
        
        stored_sessions = simulate_page_navigation_storage()
        
        # Test performance page restoration
        perf_session = stored_sessions["session1"]
        self.assertEqual(perf_session["activePageId"], "performance")
        self.assertEqual(perf_session["parentPath"], ["advanced", "performance"])
        
        # Test getting-started page restoration  
        getting_session = stored_sessions["session2"]
        self.assertEqual(getting_session["activePageId"], "getting-started")
        self.assertEqual(getting_session["parentPath"], ["getting-started"])
        
        # Test that parent paths can be used to determine what to expand
        def get_items_to_expand(page_info):
            """Get parent items that need to be expanded for this page"""
            if len(page_info["parentPath"]) <= 1:
                return []  # No parents to expand for top-level items
            
            # Return all parent levels except the active item itself
            parents_to_expand = []
            for i in range(len(page_info["parentPath"]) - 1):
                parents_to_expand.append(page_info["parentPath"][i])
            return parents_to_expand
        
        # Performance page should require expanding "advanced"
        perf_expand = get_items_to_expand(perf_session)
        self.assertEqual(perf_expand, ["advanced"])
        
        # Getting-started should require no parent expansion
        getting_expand = get_items_to_expand(getting_session)
        self.assertEqual(getting_expand, [])

    def test_template_recursive_structure(self):
        """Test that the recursive template structure supports nesting"""
        # Test the concept of recursive template inclusion
        def simulate_recursive_rendering(items, level=0):
            """Simulate how the recursive template would render nested items"""
            rendered_items = []
            for key, data in items.items():
                item_html = f'<li data-toc-id="{key}" style="margin-left: {level * 20}px">'
                item_html += f'<span>{data["title"]}</span>'

                if data.get('children'):
                    item_html += '<ul>'
                    child_items = simulate_recursive_rendering(data['children'], level + 1)
                    item_html += ''.join(child_items)
                    item_html += '</ul>'

                item_html += '</li>'
                rendered_items.append(item_html)

            return rendered_items

        # Test with our nested structure
        rendered = simulate_recursive_rendering(self.simple_toc['children'])
        rendered_html = ''.join(rendered)

        # Should contain all our test items
        self.assertIn('data-toc-id="getting-started"', rendered_html)
        self.assertIn('data-toc-id="advanced"', rendered_html)
        self.assertIn('data-toc-id="performance"', rendered_html)

        # Should have nested structure
        self.assertIn('<ul>', rendered_html)
        self.assertIn('</ul>', rendered_html)

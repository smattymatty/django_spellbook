import unittest
from unittest.mock import patch, MagicMock, PropertyMock # Added PropertyMock
import builtins 
from django.test import TestCase, override_settings
from django.conf import settings

if not settings.configured:
    settings.configure()
    import django
    django.setup()

from django_spellbook.templatetags import tag_utils

DEFAULT_USER_TEMPLATE = 'django_spellbook/metadata/for_user.html'
DEFAULT_DEV_TEMPLATE = 'django_spellbook/metadata/for_dev.html'
SETTING_NAME_METADATA_BASE = 'SPELLBOOK_MD_METADATA_BASE'
SETTING_NAME_MD_APP = 'SPELLBOOK_MD_APP'

class TestTagUtils(TestCase):

    # ... (all other test methods like test_get_metadata_template_invalid_display_type, etc., remain unchanged) ...
    def test_get_metadata_template_invalid_display_type(self):
        """Test get_metadata_template raises ValueError for invalid display_type."""
        with self.assertRaisesRegex(ValueError, "Invalid display_type: invalid. Must be 'for_user' or 'for_dev'"):
            tag_utils.get_metadata_template('invalid')

    @override_settings()
    def test_get_metadata_template_no_setting(self):
        """Test get_metadata_template with SPELLBOOK_MD_METADATA_BASE not set."""
        if hasattr(settings, SETTING_NAME_METADATA_BASE):
            delattr(settings, SETTING_NAME_METADATA_BASE)
        self.assertEqual(tag_utils.get_metadata_template('for_user'), DEFAULT_USER_TEMPLATE)
        self.assertEqual(tag_utils.get_metadata_template('for_dev'), DEFAULT_DEV_TEMPLATE)

    @override_settings(**{SETTING_NAME_METADATA_BASE: ('custom_user.html', 'custom_dev.html')})
    def test_get_metadata_template_setting_is_tuple(self):
        self.assertEqual(tag_utils.get_metadata_template('for_user'), 'custom_user.html')
        self.assertEqual(tag_utils.get_metadata_template('for_dev'), 'custom_dev.html')

    @override_settings(**{SETTING_NAME_METADATA_BASE: [
        ('app0_user.html', 'app0_dev.html'),
        ('app1_user.html', 'app1_dev.html'),
    ]})
    def test_get_metadata_template_setting_is_list_valid_index(self):
        self.assertEqual(tag_utils.get_metadata_template('for_user', app_index=0), 'app0_user.html')
        self.assertEqual(tag_utils.get_metadata_template('for_dev', app_index=0), 'app0_dev.html')
        self.assertEqual(tag_utils.get_metadata_template('for_user', app_index=1), 'app1_user.html')
        self.assertEqual(tag_utils.get_metadata_template('for_dev', app_index=1), 'app1_dev.html')

    @patch('django_spellbook.templatetags.tag_utils.logger.warning')
    @override_settings(**{SETTING_NAME_METADATA_BASE: [('app0_user.html', 'app0_dev.html')]})
    def test_get_metadata_template_setting_is_list_index_out_of_range(self, mock_logger_warning):
        self.assertEqual(tag_utils.get_metadata_template('for_user', app_index=1), DEFAULT_USER_TEMPLATE)
        mock_logger_warning.assert_any_call(
            f"App index 1 out of range for {SETTING_NAME_METADATA_BASE}. Using default template."
        )
        mock_logger_warning.assert_any_call(
            f"Invalid {SETTING_NAME_METADATA_BASE} format. Expected tuple of (user_template, dev_template) "
            f"or list of such tuples. Using default template."
        )

    @patch('django_spellbook.templatetags.tag_utils.logger.warning')
    @override_settings(**{SETTING_NAME_METADATA_BASE: ["not_a_tuple"]})
    def test_get_metadata_template_setting_is_list_invalid_item_format(self, mock_logger_warning):
        self.assertEqual(tag_utils.get_metadata_template('for_user', app_index=0), DEFAULT_USER_TEMPLATE)
        mock_logger_warning.assert_any_call(
            f"Invalid {SETTING_NAME_METADATA_BASE} format at index 0. "
            f"Expected tuple of (user_template, dev_template). Using default template."
        )
        mock_logger_warning.assert_any_call(
            f"Invalid {SETTING_NAME_METADATA_BASE} format. Expected tuple of (user_template, dev_template) "
            f"or list of such tuples. Using default template."
        )

    @patch('django_spellbook.templatetags.tag_utils.logger.warning')
    @override_settings(**{SETTING_NAME_METADATA_BASE: [('one_item_tuple',)]}) # Tuple of 1
    def test_get_metadata_template_setting_is_list_item_not_tuple_of_two(self, mock_logger_warning):
        self.assertEqual(tag_utils.get_metadata_template('for_dev', app_index=0), DEFAULT_DEV_TEMPLATE)
        mock_logger_warning.assert_any_call(
            f"Invalid {SETTING_NAME_METADATA_BASE} format at index 0. "
            f"Expected tuple of (user_template, dev_template). Using default template."
        )
        mock_logger_warning.assert_any_call(
            f"Invalid {SETTING_NAME_METADATA_BASE} format. Expected tuple of (user_template, dev_template) "
            f"or list of such tuples. Using default template."
        )

    @patch('django_spellbook.templatetags.tag_utils.logger.warning')
    @override_settings(**{SETTING_NAME_METADATA_BASE: "a_string_path"})
    def test_get_metadata_template_setting_invalid_format_string(self, mock_logger_warning):
        self.assertEqual(tag_utils.get_metadata_template('for_user'), DEFAULT_USER_TEMPLATE)
        mock_logger_warning.assert_called_once_with(
            f"Invalid {SETTING_NAME_METADATA_BASE} format. Expected tuple of (user_template, dev_template) "
            f"or list of such tuples. Using default template."
        )

    @patch('django_spellbook.templatetags.tag_utils.logger.warning')
    @override_settings(**{SETTING_NAME_METADATA_BASE: 123})
    def test_get_metadata_template_setting_invalid_format_int(self, mock_logger_warning):
        self.assertEqual(tag_utils.get_metadata_template('for_dev'), DEFAULT_DEV_TEMPLATE)
        mock_logger_warning.assert_called_once_with(
            f"Invalid {SETTING_NAME_METADATA_BASE} format. Expected tuple of (user_template, dev_template) "
            f"or list of such tuples. Using default template."
        )

    @override_settings()
    def test_get_user_metadata_template(self):
        if hasattr(settings, SETTING_NAME_METADATA_BASE):
            delattr(settings, SETTING_NAME_METADATA_BASE)
        self.assertEqual(tag_utils.get_user_metadata_template(), DEFAULT_USER_TEMPLATE)

    @override_settings(**{SETTING_NAME_METADATA_BASE: ('custom_user.html', 'custom_dev.html')})
    def test_get_user_metadata_template_with_setting(self):
        self.assertEqual(tag_utils.get_user_metadata_template(), 'custom_user.html')

    @override_settings()
    def test_get_dev_metadata_template(self):
        if hasattr(settings, SETTING_NAME_METADATA_BASE):
            delattr(settings, SETTING_NAME_METADATA_BASE)
        self.assertEqual(tag_utils.get_dev_metadata_template(), DEFAULT_DEV_TEMPLATE)

    @override_settings(**{SETTING_NAME_METADATA_BASE: ('custom_user.html', 'custom_dev.html')})
    def test_get_dev_metadata_template_with_setting(self):
        self.assertEqual(tag_utils.get_dev_metadata_template(), 'custom_dev.html')

    @patch('django_spellbook.templatetags.tag_utils.logger.warning')
    @override_settings()
    def test_get_installed_apps_no_setting(self, mock_logger_warning):
        if hasattr(settings, SETTING_NAME_MD_APP):
            delattr(settings, SETTING_NAME_MD_APP)
        self.assertEqual(tag_utils.get_installed_apps(), [])
        mock_logger_warning.assert_called_once_with(
            "SPELLBOOK_MD_APP is not set in settings. Using default template."
        )

    @patch('django_spellbook.templatetags.tag_utils.logger.warning')
    @override_settings(**{SETTING_NAME_MD_APP: None})
    def test_get_installed_apps_setting_is_none(self, mock_logger_warning):
        self.assertEqual(tag_utils.get_installed_apps(), [])
        mock_logger_warning.assert_called_once_with(
            "SPELLBOOK_MD_APP is not set in settings. Using default template."
        )

    @override_settings(**{SETTING_NAME_MD_APP: "my_single_app"})
    def test_get_installed_apps_is_string(self):
        self.assertEqual(tag_utils.get_installed_apps(), "my_single_app")

    @override_settings(**{SETTING_NAME_MD_APP: ["app1", "app2"]})
    def test_get_installed_apps_is_list(self):
        self.assertEqual(tag_utils.get_installed_apps(), ["app1", "app2"])

    @override_settings(**{SETTING_NAME_MD_APP: []})
    def test_get_installed_apps_is_empty_list(self):
        self.assertEqual(tag_utils.get_installed_apps(), [])

    # --- SIMPLIFIED test for getattr exception ---
    @patch('django_spellbook.templatetags.tag_utils.logger.error')
    @patch('django.conf.settings', new_callable=MagicMock)
    def test_get_installed_apps_setting_access_raises_exception(self, mock_settings_obj, mock_logger_error):
        """
        Test get_installed_apps when accessing SPELLBOOK_MD_APP on settings
        itself raises a non-AttributeError exception.
        """
        # Configure the 'SPELLBOOK_MD_APP' attribute on the mock_settings_obj
        # to be a PropertyMock that raises a RuntimeError when accessed.
        # This simulates a scenario where the settings object has a problematic property.
        prop_that_raises_error = PropertyMock(side_effect=RuntimeError("Simulated settings property failure"))

        # To make getattr(mock_settings_obj, 'SPELLBOOK_MD_APP', ...) trigger this,
        # we assign this PropertyMock to the attribute name on the type of the mock_settings_obj.
        type(mock_settings_obj).SPELLBOOK_MD_APP = prop_that_raises_error

        # Now, when tag_utils.get_installed_apps() calls:
        #   getattr(settings, 'SPELLBOOK_MD_APP', None)
        # ...it will use our mock_settings_obj. Accessing 'SPELLBOOK_MD_APP'
        # on it will trigger the PropertyMock's side_effect (RuntimeError).
        # This RuntimeError should be caught by the `except Exception` block.

        result = tag_utils.get_installed_apps()

        self.assertEqual(result, []) # Expect default empty list on error
        mock_logger_error.assert_called_once()
        logged_message = mock_logger_error.call_args[0][0]
        expected_error_message = f"Error getting {SETTING_NAME_MD_APP} from settings: Simulated settings property failure"
        self.assertIn(expected_error_message, logged_message)

        # Clean up the type-level patch to prevent interference with other tests,
        # though new_callable=MagicMock usually isolates the mock instance.
        # It's good practice if there's any doubt.
        delattr(type(mock_settings_obj), 'SPELLBOOK_MD_APP')


    def test_get_current_app_index_context_none(self):
        self.assertEqual(tag_utils.get_current_app_index(None), 0)

    def test_get_current_app_index_no_metadata_in_context(self):
        context = {}
        self.assertEqual(tag_utils.get_current_app_index(context), 0)

    def test_get_current_app_index_metadata_not_dict(self):
        context = {'metadata': "not_a_dict"}
        self.assertEqual(tag_utils.get_current_app_index(context), 0)

    def test_get_current_app_index_no_namespace_in_metadata(self):
        context = {'metadata': {}}
        self.assertEqual(tag_utils.get_current_app_index(context), 0)

    def test_get_current_app_index_empty_namespace_in_metadata(self):
        context = {'metadata': {'namespace': ''}}
        self.assertEqual(tag_utils.get_current_app_index(context), 0)

    @patch('django_spellbook.templatetags.tag_utils.get_installed_apps', return_value="single_app_name")
    def test_get_current_app_index_installed_apps_is_string(self, mock_get_installed_apps):
        context = {'metadata': {'namespace': 'single_app_name'}}
        self.assertEqual(tag_utils.get_current_app_index(context), 0)
        mock_get_installed_apps.assert_called_once()

    @patch('django_spellbook.templatetags.tag_utils.get_installed_apps', return_value=None)
    def test_get_current_app_index_installed_apps_is_none(self, mock_get_installed_apps):
        context = {'metadata': {'namespace': 'app1'}}
        self.assertEqual(tag_utils.get_current_app_index(context), 0)
        mock_get_installed_apps.assert_called_once()

    @patch('django_spellbook.templatetags.tag_utils.get_installed_apps', return_value=['app1', 'app2', 'app3'])
    def test_get_current_app_index_namespace_found(self, mock_get_installed_apps):
        context = {'metadata': {'namespace': 'app2'}}
        self.assertEqual(tag_utils.get_current_app_index(context), 1)
        mock_get_installed_apps.assert_called_once()

    @patch('django_spellbook.templatetags.tag_utils.get_installed_apps', return_value=['app1', 'app2'])
    def test_get_current_app_index_namespace_not_found(self, mock_get_installed_apps):
        context = {'metadata': {'namespace': 'app_not_in_list'}}
        self.assertEqual(tag_utils.get_current_app_index(context), 0)
        mock_get_installed_apps.assert_called_once()

    @patch('django_spellbook.templatetags.tag_utils.get_installed_apps', return_value=[])
    def test_get_current_app_index_installed_apps_empty_list(self, mock_get_installed_apps):
        context = {'metadata': {'namespace': 'app1'}}
        self.assertEqual(tag_utils.get_current_app_index(context), 0)
        mock_get_installed_apps.assert_called_once()


if __name__ == '__main__':
    unittest.main()
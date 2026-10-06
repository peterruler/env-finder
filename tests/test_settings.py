import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app import create_app
import settings
import start


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name).resolve()
        self.folder = self.project / 'search folder'
        self.folder.mkdir()
        self.env_file = self.project / '.env'
        self.env_file.write_text(f'DEFAULT_SEARCH_FOLDER="{self.folder}" # Standard\n')
        self.project_patch = patch.object(settings, 'PROJECT', self.project)
        self.project_patch.start()
        self.addCleanup(self.project_patch.stop)
        self.environment_patch = patch.dict(os.environ, {}, clear=True)
        self.environment_patch.start()
        self.addCleanup(self.environment_patch.stop)

    def test_app_and_starter_load_same_configuration_from_other_cwd(self):
        previous = Path.cwd()
        elsewhere = self.project / 'elsewhere'
        elsewhere.mkdir()
        try:
            os.chdir(elsewhere)
            self.assertEqual(create_app().test_client().get('/api/directories').json['path'], str(self.folder))
            with patch('sys.argv', ['start.py', '--docker']), patch.object(start, 'start_docker') as launch:
                start.main()
            launch.assert_called_once_with(self.folder, self.folder, 5000)
        finally:
            os.chdir(previous)

    def test_environment_and_explicit_arguments_override_file(self):
        alternate = self.project / 'alternate'
        alternate.mkdir()
        with patch.dict(os.environ, {'DEFAULT_SEARCH_FOLDER': str(alternate)}):
            self.assertEqual(settings.default_search_folder(), alternate)
            self.assertEqual(create_app().test_client().get('/api/directories').json['path'], str(alternate))
            with patch('sys.argv', ['start.py', '--root', str(self.folder)]), patch.object(start, 'start_docker') as launch:
                start.main()
            launch.assert_called_once_with(self.folder, self.folder, 5000)

    def test_missing_and_empty_setting_require_configuration(self):
        self.env_file.unlink()
        with self.assertRaisesRegex(RuntimeError, 'DEFAULT_SEARCH_FOLDER fehlt'):
            create_app()
        self.env_file.write_text('DEFAULT_SEARCH_FOLDER=\n')
        with self.assertRaisesRegex(RuntimeError, 'DEFAULT_SEARCH_FOLDER fehlt'):
            settings.default_search_folder()
        self.assertEqual(create_app(self.folder, self.folder).test_client().get('/health').status_code, 200)
        with patch('sys.argv', ['start.py', '--root', str(self.folder)]), patch.object(start, 'start_docker') as launch:
            start.main()
        launch.assert_called_once_with(self.folder, self.folder, 5000)

    def test_relative_path_is_resolved_against_configuration_directory(self):
        self.env_file.write_text('export DEFAULT_SEARCH_FOLDER=search folder # Kommentar\n')
        self.assertEqual(settings.default_search_folder(), self.folder)

    def test_container_root_override_does_not_require_host_dotenv(self):
        self.env_file.unlink()
        with patch.dict(os.environ, {'ENV_FINDER_ROOT': str(self.folder)}):
            self.assertEqual(create_app().test_client().get('/api/directories').json['path'], str(self.folder))


if __name__ == '__main__':
    unittest.main()

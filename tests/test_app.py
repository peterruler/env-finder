import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

import app as application


class FinderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / 'project' / '.hidden').mkdir(parents=True)
        (self.root / '.env').write_text('SECRET=should-never-be-returned')
        (self.root / 'project' / '.env').write_text('SECOND=private')
        (self.root / 'project' / '.hidden' / '.env').write_text('HIDDEN=private')
        (self.root / 'project' / '.env.local').write_text('LOCAL=private')
        (self.root / 'project' / 'regular.txt').write_text('normal')
        self.client = application.create_app(self.root, self.root).test_client()

    def test_recursive_exact_names_and_no_values(self):
        response = self.client.get('/api/search')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['count'], 3)
        self.assertFalse(response.json['truncated'])
        self.assertNotIn('SECOND=private', response.get_data(as_text=True))
        self.assertNotIn('should-never-be-returned', response.get_data(as_text=True))
        self.assertNotIn('SECRET', response.get_data(as_text=True))
        self.assertTrue(all(item['name'] == '.env' for item in response.json['files']))

    def test_optional_variants_and_selected_subdirectory(self):
        data = self.client.get('/api/search', query_string={'path': 'project', 'variants': 'true'}).json
        self.assertEqual(data['count'], 3)
        self.assertIn('.env.local', [item['name'] for item in data['files']])

    def test_contents_are_returned_as_text_without_parsing(self):
        text = '# Kommentar\nNAME="Grüezi"\nHTML=<script>example()</script>\n'
        (self.root / '.env').write_text(text, encoding='utf-8')
        response = self.client.get('/api/content?path=.env')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['content'], text)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertEqual(response.json['warnings'], [])
        self.assertFalse(response.json['truncated'])
        self.assertEqual(self.client.get('/api/content?path=project/.env.local').json['content'], 'LOCAL=private')

    def test_content_rejects_other_files_and_symlinks(self):
        (self.root / '.env.link').symlink_to(self.root / '.env')
        (self.root / 'linked-project').symlink_to(self.root / 'project', target_is_directory=True)
        for path in ('project/regular.txt', '.env.link', 'linked-project/.env', '..', '/etc/passwd', 'missing/.env', ''):
            self.assertEqual(self.client.get('/api/content', query_string={'path': path}).status_code, 400, path)

    def test_content_handles_empty_bom_invalid_utf8_and_limits(self):
        path = self.root / '.env'
        path.write_bytes(b'')
        self.assertEqual(self.client.get('/api/content?path=.env').json['content'], '')
        path.write_bytes(b'\xef\xbb\xbfNAME=value\n')
        self.assertEqual(self.client.get('/api/content?path=.env').json['content'], 'NAME=value\n')
        path.write_bytes(b'NAME=\xff')
        data = self.client.get('/api/content?path=.env').json
        self.assertEqual(data['content'], 'NAME=\ufffd')
        self.assertTrue(data['warnings'])
        path.write_bytes(b'123456789')
        with patch.object(application, 'MAX_CONTENT_BYTES', 5):
            data = self.client.get('/api/content?path=.env').json
        self.assertEqual(data['content'], '12345')
        self.assertTrue(data['truncated'])
        self.assertTrue(data['warnings'])

    def test_unreadable_content_returns_per_file_error(self):
        with patch.object(application.os, 'open', side_effect=PermissionError('test')):
            response = self.client.get('/api/content?path=.env')
        self.assertEqual(response.status_code, 403)
        self.assertIn('Leseberechtigung', response.json['error'])

    def test_picker_navigation(self):
        data = self.client.get('/api/directories').json
        self.assertIsNone(data['parent'])
        self.assertEqual([entry['name'] for entry in data['directories']], ['project'])
        child = self.client.get('/api/directories', query_string={'path': 'project'}).json
        self.assertEqual(child['parent'], str(self.root))

    def test_path_escape_and_missing_path(self):
        for endpoint in ('/api/search', '/api/directories'):
            for path in ('..', '/does-not-exist', str(self.root / 'regular-missing')):
                self.assertEqual(self.client.get(endpoint, query_string={'path': path}).status_code, 400)
            self.assertEqual(self.client.get(endpoint, query_string={'path': '.env'}).status_code, 400)

    def test_symlinks_not_followed(self):
        (self.root / 'linked-directory').symlink_to(self.root / 'project', target_is_directory=True)
        (self.root / 'project' / '.env.link').symlink_to(self.root / '.env')
        self.assertEqual(self.client.get('/api/search?variants=true').json['count'], 4)
        self.assertNotIn('linked-directory', [entry['name'] for entry in self.client.get('/api/directories').json['directories']])
        (self.root / 'outside').symlink_to(self.root.parent, target_is_directory=True)
        self.assertEqual(self.client.get('/api/search?path=outside').status_code, 400)

    def test_host_paths_in_docker_mode(self):
        with patch.dict(os.environ, {'ENV_FINDER_HOST_ROOT': '/host/Projects'}):
            client = application.create_app(self.root, self.root).test_client()
            data = client.get('/api/search').json
            self.assertEqual(data['directory'], '/host/Projects')
            self.assertIn('/host/Projects/.env', [item['path'] for item in data['files']])
            self.assertEqual(client.get('/api/search?path=/host/Projects/project').json['count'], 2)
            self.assertEqual(client.get('/api/directories').json['directories'][0]['path'], '/host/Projects/project')
            self.assertEqual(client.get('/api/directories?path=/host/Projects/project').json['parent'], '/host/Projects')
            self.assertEqual(client.get('/api/search?path=/host/other').status_code, 400)
            self.assertEqual(client.get('/api/content?path=/host/Projects/project/.env').json['content'], 'SECOND=private')

    def test_partial_result_limits(self):
        with patch.object(application, 'MAX_RESULTS', 1):
            data = self.client.get('/api/search').json
            self.assertEqual(data['count'], 1)
            self.assertTrue(data['truncated'])
            self.assertTrue(data['warnings'])
        with patch.object(application, 'MAX_SCAN_SECONDS', 0):
            self.assertFalse(self.client.get('/api/search').json['truncated'])
            data = self.client.get('/api/search?bounded=true').json
            self.assertTrue(data['truncated'])
            self.assertTrue(data['warnings'])

    def test_unreadable_subdirectory_warns(self):
        original = os.scandir

        def scan(path):
            if Path(path) == self.root / 'project':
                raise PermissionError('test')
            return original(path)

        with patch.object(application.os, 'scandir', side_effect=scan):
            data = self.client.get('/api/search').json
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['skipped'], 1)
        self.assertTrue(data['warnings'])

    def test_html_health_and_host_validation(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/health').json, {'status': 'ok'})
        self.assertEqual(self.client.get('/health', headers={'Host': 'untrusted.example'}).status_code, 400)

    def test_occupied_port_falls_back_and_reserves_listener(self):
        with socket.socket() as occupied:
            occupied.bind(('127.0.0.1', 0))
            occupied.listen()
            port = occupied.getsockname()[1]
            with application.bind_available('127.0.0.1', port) as reserved:
                self.assertNotEqual(reserved.getsockname()[1], port)
                with socket.create_connection(reserved.getsockname(), timeout=1):
                    pass


if __name__ == '__main__':
    unittest.main()

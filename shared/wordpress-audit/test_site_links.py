"""Offline regression tests; never contacts or modifies a website."""
import unittest
from unittest.mock import patch
import auditoria_wordpress as audit


class SiteLinksTests(unittest.TestCase):
    def tearDown(self):
        audit.configure_site('https://ephemerajpp.com')

    def test_configured_hosts(self):
        cases = [
            ('https://ephemerajpp.com', 'https://ephemerajpp.com/post', True),
            ('https://www.acad-ciencias.pt', 'https://acad-ciencias.pt/page', True),
            ('https://www.acad-ciencias.pt', 'https://biblioteca.acad-ciencias.pt/', True),
            ('https://www.acad-ciencias.pt', 'https://ephemerajpp.com/', False),
            ('https://example.org/blog', 'http://WWW.EXAMPLE.ORG:8080/a', True),
            ('https://example.org', 'https://example.org.evil.test/', False),
            ('https://example.org', 'https://notexample.org/', False),
            ('https://example.org', 'https://example.org@evil.test/', False),
            ('https://example.org', 'mailto:person@example.org', False),
            ('https://example.org', '/relative', False),
            ('https://example.org', 'https://example.org./page', True),
            ('https://blog.example.org', 'https://other.example.org/', False),
        ]
        for base, target, expected in cases:
            with self.subTest(base=base, target=target):
                audit.configure_site(base)
                self.assertEqual(audit.is_internal_url(target), expected)

    def test_extracted_links_use_configured_site(self):
        audit.configure_site('https://www.acad-ciencias.pt')
        data = {'pages': [{'id': 1, 'link': 'https://www.acad-ciencias.pt/a',
                          'title': {'rendered': 'Example'},
                          'content': {'rendered': '<a href="/b">Internal</a><a href="https://ephemerajpp.com/">External</a>'}}]}
        with patch.object(audit, 'load_spellcheckers', return_value={}):
            result = audit.analyze(data, [], {})
        self.assertEqual([x['Interno'] for x in result['links']], [True, False])

    def test_link_selection_and_results_use_configured_site(self):
        audit.configure_site('https://www.acad-ciencias.pt')
        result = {'links': [{'URL destino': 'https://ephemerajpp.com/', 'Origem': 'source'},
                            {'URL destino': 'https://www.acad-ciencias.pt/b', 'Origem': 'source'}]}
        with patch.object(audit, 'urlopen') as request, patch.object(audit.time, 'sleep'):
            response = request.return_value.__enter__.return_value
            response.status = 200
            response.geturl.return_value = 'https://www.acad-ciencias.pt/b'
            checked = audit.check_links(result, max_internal=1, max_external=0)
        self.assertEqual(len(checked), 1)
        self.assertEqual(checked[0]['URL'], 'https://www.acad-ciencias.pt/b')
        self.assertTrue(checked[0]['Interno'])


if __name__ == '__main__':
    unittest.main()

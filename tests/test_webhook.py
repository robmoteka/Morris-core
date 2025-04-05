import unittest
import json
import sys
import os
from flask import Flask
from unittest.mock import patch, MagicMock

# Dodanie katalogu głównego projektu do ścieżki, aby umożliwić import modułów
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from routes.webhook import webhook_bp

class TestWebhook(unittest.TestCase):
    """
    Klasa testowa dla modułu webhook.
    Testuje funkcjonalność obsługi webhooków w aplikacji Morris.
    """
    
    def setUp(self):
        """
        Przygotowanie środowiska testowego przed każdym testem.
        Tworzy testową aplikację Flask z zarejestrowanym blueprintem webhook.
        """
        self.app = Flask(__name__)
        self.app.register_blueprint(webhook_bp)
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True
    
    def test_webhook_valid_json(self):
        """
        Test sprawdzający poprawne przetwarzanie danych JSON przez webhook.
        """
        # Przygotowanie testowych danych JSON
        testData = {
            "message": "Test webhook",
            "value": 123,
            "timestamp": "2025-04-05T12:00:00Z"
        }
        
        # Wysłanie zapytania POST z danymi JSON
        response = self.client.post(
            '/hook/test',
            data=json.dumps(testData),
            content_type='application/json'
        )
        
        # Sprawdzenie odpowiedzi
        self.assertEqual(response.status_code, 200)
        responseData = json.loads(response.data)
        self.assertEqual(responseData['status'], 'success')
        self.assertIn('test', responseData['message'])
    
    def test_webhook_invalid_data(self):
        """
        Test sprawdzający obsługę nieprawidłowych danych (nie JSON) przez webhook.
        """
        # Wysłanie zapytania POST z danymi, które nie są w formacie JSON
        response = self.client.post(
            '/hook/test',
            data='To nie jest JSON',
            content_type='text/plain'
        )
        
        # Sprawdzenie odpowiedzi
        self.assertEqual(response.status_code, 400)
        responseData = json.loads(response.data)
        self.assertEqual(responseData['status'], 'error')
        self.assertIn('JSON', responseData['message'])
    
    def test_webhook_different_modules(self):
        """
        Test sprawdzający obsługę webhooków dla różnych modułów.
        """
        # Przygotowanie testowych danych JSON
        testData = {
            "message": "Test webhook",
            "value": 123
        }
        
        # Lista modułów do przetestowania
        moduły = ['test', 'sensor', 'device', 'alert']
        
        for moduł in moduły:
            # Wysłanie zapytania POST z danymi JSON do różnych modułów
            response = self.client.post(
                f'/hook/{moduł}',
                data=json.dumps(testData),
                content_type='application/json'
            )
            
            # Sprawdzenie odpowiedzi
            self.assertEqual(response.status_code, 200)
            responseData = json.loads(response.data)
            self.assertEqual(responseData['status'], 'success')
            self.assertIn(moduł, responseData['message'])

if __name__ == '__main__':
    unittest.main()

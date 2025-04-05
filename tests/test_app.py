import unittest
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Dodanie katalogu głównego projektu do ścieżki, aby umożliwić import modułów
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import aplikacji z mockiem dla MqttClient
with patch('app.MqttClient') as mockMqttClient:
    mockMqttClientInstance = MagicMock()
    mockMqttClient.return_value = mockMqttClientInstance
    import app

class TestApp(unittest.TestCase):
    """
    Klasa testowa dla głównej aplikacji Flask.
    Testuje funkcjonalność endpointów i integrację komponentów.
    """
    
    def setUp(self):
        """
        Przygotowanie środowiska testowego przed każdym testem.
        """
        # Konfiguracja klienta testowego
        self.app = app.app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Zastąpienie rzeczywistego klienta MQTT mockiem
        app.mqtt_client = mockMqttClientInstance
    
    def test_index_endpoint(self):
        """
        Test sprawdzający endpoint główny (/).
        """
        # Wysłanie zapytania GET do głównego endpointu
        response = self.client.get('/')
        
        # Sprawdzenie odpowiedzi
        self.assertEqual(response.status_code, 200)
        responseData = json.loads(response.data)
        
        # Sprawdzenie zawartości odpowiedzi
        self.assertEqual(responseData['status'], 'running')
        self.assertEqual(responseData['app'], 'Morris Core')
        self.assertIn('version', responseData)
        self.assertIn('endpoints', responseData)
        self.assertIn('webhook', responseData['endpoints'])
        self.assertIn('test_mqtt', responseData['endpoints'])
    
    def test_send_test_endpoint_success(self):
        """
        Test sprawdzający endpoint /send-test przy udanej publikacji MQTT.
        """
        # Konfiguracja mocka - udana publikacja
        mockMqttClientInstance.publish.return_value = True
        
        # Wysłanie zapytania GET do endpointu /send-test
        response = self.client.get('/send-test')
        
        # Sprawdzenie odpowiedzi
        self.assertEqual(response.status_code, 200)
        responseData = json.loads(response.data)
        
        # Sprawdzenie zawartości odpowiedzi
        self.assertEqual(responseData['status'], 'success')
        self.assertIn('Opublikowano', responseData['message'])
        self.assertIn('data', responseData)
        self.assertEqual(responseData['data']['source'], 'morris_core')
        self.assertEqual(responseData['data']['action'], 'test')
        self.assertIn('timestamp', responseData['data'])
        self.assertIn('data', responseData['data'])
        self.assertEqual(responseData['data']['data']['value'], 42)
    
    def test_send_test_endpoint_failure(self):
        """
        Test sprawdzający endpoint /send-test przy nieudanej publikacji MQTT.
        """
        # Konfiguracja mocka - nieudana publikacja
        mockMqttClientInstance.publish.return_value = False
        
        # Wysłanie zapytania GET do endpointu /send-test
        response = self.client.get('/send-test')
        
        # Sprawdzenie odpowiedzi
        self.assertEqual(response.status_code, 500)
        responseData = json.loads(response.data)
        
        # Sprawdzenie zawartości odpowiedzi
        self.assertEqual(responseData['status'], 'error')
        self.assertIn('Nie udało się', responseData['message'])
    
    @patch('app.datetime')
    def test_timestamp_in_send_test(self, mockDatetime):
        """
        Test sprawdzający generowanie timestampu w endpoincie /send-test.
        """
        # Konfiguracja mocka - udana publikacja i stały timestamp
        mockMqttClientInstance.publish.return_value = True
        mockDatetime.now.return_value.isoformat.return_value = '2025-04-05T12:00:00'
        
        # Wysłanie zapytania GET do endpointu /send-test
        response = self.client.get('/send-test')
        
        # Sprawdzenie odpowiedzi
        self.assertEqual(response.status_code, 200)
        responseData = json.loads(response.data)
        
        # Sprawdzenie timestampu w odpowiedzi
        self.assertEqual(responseData['data']['timestamp'], '2025-04-05T12:00:00')

if __name__ == '__main__':
    unittest.main()

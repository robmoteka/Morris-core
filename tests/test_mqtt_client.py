import unittest
import json
import sys
import os
import tempfile
from unittest.mock import patch, MagicMock, mock_open

# Dodanie katalogu głównego projektu do ścieżki, aby umożliwić import modułów
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mqtt_client import MqttClient

class TestMqttClient(unittest.TestCase):
    """
    Klasa testowa dla modułu MqttClient.
    Testuje funkcjonalność klienta MQTT w aplikacji Morris.
    """
    
    def setUp(self):
        """
        Przygotowanie środowiska testowego przed każdym testem.
        """
        # Przygotowanie testowej konfiguracji MQTT
        self.testConfig = {
            "broker": "test.mosquitto.org",
            "port": 1883,
            "client_id": "test_client",
            "keepalive": 60,
            "topics": {
                "subscribe": ["test/#"],
                "publish": "test/output"
            },
            "username": "",
            "password": ""
        }
        
        # Utworzenie tymczasowego pliku konfiguracyjnego
        self.tempConfigFile = tempfile.NamedTemporaryFile(delete=False, mode='w+')
        json.dump(self.testConfig, self.tempConfigFile)
        self.tempConfigFile.close()
    
    def tearDown(self):
        """
        Czyszczenie po testach.
        """
        # Usunięcie tymczasowego pliku konfiguracyjnego
        if hasattr(self, 'tempConfigFile'):
            os.unlink(self.tempConfigFile.name)
    
    @patch('mqtt_client.mqtt_client.Client')
    def test_mqtt_client_initialization(self, mockClient):
        """
        Test sprawdzający poprawną inicjalizację klienta MQTT.
        """
        # Utworzenie instancji klienta MQTT z mockiem
        mqttClient = MqttClient(config_path=self.tempConfigFile.name)
        
        # Sprawdzenie, czy konfiguracja została poprawnie wczytana
        self.assertEqual(mqttClient.config["broker"], self.testConfig["broker"])
        self.assertEqual(mqttClient.config["port"], self.testConfig["port"])
        # Client ID będzie miał dodany losowy sufiks, więc sprawdzamy tylko początek
        self.assertTrue(mqttClient.config["client_id"].startswith(self.testConfig["client_id"]))
    
    @patch('mqtt_client.mqtt_client.Client')
    def test_mqtt_client_start_stop(self, mockClient):
        """
        Test sprawdzający uruchamianie i zatrzymywanie klienta MQTT.
        """
        # Konfiguracja mocka
        mockClientInstance = MagicMock()
        mockClient.return_value = mockClientInstance
        
        # Utworzenie instancji klienta MQTT z mockiem
        mqttClient = MqttClient(config_path=self.tempConfigFile.name)
        
        # Uruchomienie klienta
        mqttClient.start()
        
        # Sprawdzenie, czy metody klienta zostały wywołane
        self.assertTrue(mqttClient.running)
        self.assertIsNotNone(mqttClient.thread)
        
        # Zatrzymanie klienta
        mqttClient.stop()
        
        # Sprawdzenie, czy klient został zatrzymany
        self.assertFalse(mqttClient.running)
    
    @patch('mqtt_client.mqtt_client.Client')
    def test_mqtt_client_publish(self, mockClient):
        """
        Test sprawdzający publikację wiadomości MQTT.
        """
        # Konfiguracja mocka
        mockClientInstance = MagicMock()
        mockResult = MagicMock()
        mockResult.rc = 0  # Kod sukcesu
        mockClientInstance.publish.return_value = mockResult
        mockClient.return_value = mockClientInstance
        
        # Utworzenie instancji klienta MQTT z mockiem
        mqttClient = MqttClient(config_path=self.tempConfigFile.name)
        
        # Symulacja połączenia klienta
        mqttClient.client = mockClientInstance
        mqttClient.connected = True
        
        # Testowe dane do publikacji
        testTopic = "test/custom"
        testPayload = {"message": "Test message", "value": 42}
        
        # Publikacja wiadomości
        result = mqttClient.publish(topic=testTopic, payload=testPayload)
        
        # Sprawdzenie, czy publikacja się powiodła
        self.assertTrue(result)
        mockClientInstance.publish.assert_called_once()
        # Sprawdzenie argumentów wywołania
        args, kwargs = mockClientInstance.publish.call_args
        self.assertEqual(args[0], testTopic)
        self.assertEqual(json.loads(args[1]), testPayload)
    
    @patch('mqtt_client.mqtt_client.Client')
    def test_mqtt_client_callbacks(self, mockClient):
        """
        Test sprawdzający działanie callbacków klienta MQTT.
        """
        # Konfiguracja mocka
        mockClientInstance = MagicMock()
        mockClient.return_value = mockClientInstance
        
        # Utworzenie instancji klienta MQTT z mockiem
        mqttClient = MqttClient(config_path=self.tempConfigFile.name)
        mqttClient.client = mockClientInstance
        
        # Testowanie callbacka on_connect
        mqttClient._on_connect(mockClientInstance, None, None, 0)
        self.assertTrue(mqttClient.connected)
        
        # Testowanie callbacka on_disconnect
        mqttClient._on_disconnect(mockClientInstance, None, 0)
        self.assertFalse(mqttClient.connected)
        
        # Testowanie callbacka on_message
        mockMsg = MagicMock()
        mockMsg.topic = "test/topic"
        mockMsg.payload = b'{"message": "Test message"}'
        mqttClient._on_message(mockClientInstance, None, mockMsg)
        # Nie ma bezpośredniego sposobu na sprawdzenie, czy wiadomość została zalogowana,
        # ale możemy sprawdzić, czy nie wystąpił żaden wyjątek
    
    @patch('mqtt_client.open', new_callable=mock_open, read_data='{"invalid": "json"')
    def test_mqtt_client_load_invalid_config(self, mockOpen):
        """
        Test sprawdzający obsługę nieprawidłowego pliku konfiguracyjnego.
        """
        # Utworzenie instancji klienta MQTT z mockiem nieprawidłowego pliku
        mqttClient = MqttClient(config_path="invalid_path.json")
        
        # Sprawdzenie, czy została użyta domyślna konfiguracja
        self.assertEqual(mqttClient.config["broker"], "broker.emqx.io")
        self.assertEqual(mqttClient.config["port"], 1883)

if __name__ == '__main__':
    unittest.main()

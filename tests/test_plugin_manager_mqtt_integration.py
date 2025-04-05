#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Testy integracyjne dla modułu Plugin Manager z MQTT.
Testuje komunikację między PluginManager a klientem MQTT.
"""

import unittest
import json
import os
import tempfile
import time
import sys
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

# Dodanie katalogu głównego do ścieżki, aby umożliwić importowanie modułów
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from plugins.manager import PluginManager
from mqtt_client import MqttClient

class PluginManagerMqttIntegrationTest(unittest.TestCase):
    """
    Testy integracyjne dla współpracy PluginManager z MQTT.
    """
    
    def setUp(self):
        """
        Przygotowanie środowiska testowego przed każdym testem.
        """
        # Utworzenie tymczasowego pliku dla danych wtyczek
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        
        # Utworzenie mocka dla klienta MQTT z odpowiednią konfiguracją
        self.mqtt_client_mock = MagicMock()
        self.mqtt_client_mock.config = {
            "topics": {
                "subscribe": ["plugin/announce"]
            }
        }
        self.mqtt_client_mock.client = MagicMock()
        self.mqtt_client_mock.connected = True
        
        # Utworzenie instancji PluginManager do testów
        self.plugin_manager = PluginManager(
            mqtt_client=self.mqtt_client_mock,
            plugins_file=self.temp_file.name,
            offline_timeout=1  # Krótki timeout dla testów
        )
    
    def tearDown(self):
        """
        Czyszczenie po każdym teście.
        """
        # Usunięcie tymczasowego pliku
        os.unlink(self.temp_file.name)
    
    def test_mqtt_subscription_setup(self):
        """
        Test poprawności konfiguracji subskrypcji MQTT.
        """
        # Sprawdzenie, czy metoda message_callback_add została wywołana z odpowiednim tematem
        self.mqtt_client_mock.client.message_callback_add.assert_called_with(
            "plugin/announce", 
            self.plugin_manager._handle_plugin_announcement
        )
        
        # Sprawdzenie, czy metoda subscribe została wywołana
        self.mqtt_client_mock.client.subscribe.assert_called_with("plugin/announce")
    
    def test_mqtt_announcement_handling(self):
        """
        Test obsługi ogłoszenia wtyczki przez MQTT.
        """
        # Dane testowej wtyczki
        plugin_data = {
            "name": "mqtt_test_plugin",
            "type": "mqtt",
            "description": "Testowa wtyczka MQTT",
            "status": "online"
        }
        
        # Symulacja otrzymania wiadomości MQTT
        message_mock = MagicMock()
        message_mock.topic = "plugin/announce"
        message_mock.payload = json.dumps(plugin_data).encode('utf-8')
        
        # Wywołanie callbacka
        self.plugin_manager._handle_plugin_announcement(None, None, message_mock)
        
        # Sprawdzenie, czy wtyczka została zarejestrowana
        plugins = self.plugin_manager.get_plugins()
        self.assertIn("mqtt_test_plugin", plugins)
        self.assertEqual(plugins["mqtt_test_plugin"]["type"], "mqtt")
        self.assertEqual(plugins["mqtt_test_plugin"]["description"], "Testowa wtyczka MQTT")
        self.assertEqual(plugins["mqtt_test_plugin"]["status"], "online")
    
    def test_mqtt_invalid_message_handling(self):
        """
        Test obsługi nieprawidłowej wiadomości MQTT.
        """
        # Symulacja otrzymania nieprawidłowej wiadomości MQTT (nieprawidłowy JSON)
        message_mock = MagicMock()
        message_mock.topic = "plugin/announce"
        message_mock.payload = b"nieprawidlowy json"
        
        # Wywołanie callbacka
        self.plugin_manager._handle_plugin_announcement(None, None, message_mock)
        
        # Sprawdzenie, czy słownik wtyczek jest nadal pusty
        plugins = self.plugin_manager.get_plugins()
        self.assertEqual(len(plugins), 0)
    
    def test_mqtt_missing_fields_handling(self):
        """
        Test obsługi wiadomości MQTT z brakującymi polami.
        """
        # Dane niepełnej wtyczki (brak pola 'status')
        plugin_data = {
            "name": "incomplete_plugin",
            "type": "mqtt",
            "description": "Niepełna wtyczka MQTT"
        }
        
        # Symulacja otrzymania wiadomości MQTT
        message_mock = MagicMock()
        message_mock.topic = "plugin/announce"
        message_mock.payload = json.dumps(plugin_data).encode('utf-8')
        
        # Wywołanie callbacka
        self.plugin_manager._handle_plugin_announcement(None, None, message_mock)
        
        # Sprawdzenie, czy wtyczka nie została zarejestrowana
        plugins = self.plugin_manager.get_plugins()
        self.assertNotIn("incomplete_plugin", plugins)
    
    @patch('plugins.manager.datetime')
    def test_plugin_status_update(self, mock_datetime):
        """
        Test aktualizacji statusu wtyczki.
        """
        # Rejestracja testowej wtyczki
        plugin_data = {
            "name": "update_test_plugin",
            "type": "mqtt",
            "description": "Wtyczka do testowania aktualizacji",
            "status": "online"
        }
        self.plugin_manager.register_plugin(plugin_data)
        
        # Sprawdzenie początkowego statusu
        plugins = self.plugin_manager.get_plugins()
        self.assertEqual(plugins["update_test_plugin"]["status"], "online")
        
        # Aktualizacja danych wtyczki
        updated_data = {
            "name": "update_test_plugin",
            "type": "mqtt",
            "description": "Zaktualizowana wtyczka",
            "status": "busy"
        }
        
        # Symulacja otrzymania wiadomości MQTT z aktualizacją
        message_mock = MagicMock()
        message_mock.topic = "plugin/announce"
        message_mock.payload = json.dumps(updated_data).encode('utf-8')
        
        # Wywołanie callbacka
        self.plugin_manager._handle_plugin_announcement(None, None, message_mock)
        
        # Sprawdzenie, czy dane wtyczki zostały zaktualizowane
        plugins = self.plugin_manager.get_plugins()
        self.assertEqual(plugins["update_test_plugin"]["description"], "Zaktualizowana wtyczka")
        self.assertEqual(plugins["update_test_plugin"]["status"], "busy")

if __name__ == '__main__':
    unittest.main()

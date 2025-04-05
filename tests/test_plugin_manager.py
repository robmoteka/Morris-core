#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Testy jednostkowe dla modułu Plugin Manager.
"""

import unittest
import json
import os
import tempfile
import time
from unittest.mock import MagicMock, patch
import sys
from datetime import datetime, timedelta

# Dodanie katalogu głównego do ścieżki, aby umożliwić importowanie modułów
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from plugins.manager import PluginManager

class PluginManagerTest(unittest.TestCase):
    """
    Testy jednostkowe dla klasy PluginManager.
    """
    
    def setUp(self):
        """
        Przygotowanie środowiska testowego przed każdym testem.
        """
        # Utworzenie tymczasowego pliku dla danych wtyczek
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        
        # Utworzenie mocka dla klienta MQTT
        self.mqtt_client_mock = MagicMock()
        
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
    
    def test_register_plugin(self):
        """
        Test rejestracji wtyczki.
        """
        # Dane testowej wtyczki
        plugin_data = {
            "name": "test_plugin",
            "type": "local",
            "description": "Testowa wtyczka",
            "status": "online"
        }
        
        # Rejestracja wtyczki
        success = self.plugin_manager.register_plugin(plugin_data)
        
        # Sprawdzenie, czy operacja się powiodła
        self.assertTrue(success)
        
        # Sprawdzenie, czy wtyczka została dodana do słownika
        plugins = self.plugin_manager.get_plugins()
        self.assertIn("test_plugin", plugins)
        self.assertEqual(plugins["test_plugin"]["type"], "local")
        self.assertEqual(plugins["test_plugin"]["description"], "Testowa wtyczka")
        self.assertEqual(plugins["test_plugin"]["status"], "online")
        self.assertIn("last_seen", plugins["test_plugin"])
    
    def test_register_invalid_plugin(self):
        """
        Test rejestracji wtyczki z niepełnymi danymi.
        """
        # Niepełne dane wtyczki (brak pola 'status')
        plugin_data = {
            "name": "invalid_plugin",
            "type": "local",
            "description": "Niepełna wtyczka"
        }
        
        # Próba rejestracji wtyczki
        success = self.plugin_manager.register_plugin(plugin_data)
        
        # Sprawdzenie, czy operacja się nie powiodła
        self.assertFalse(success)
        
        # Sprawdzenie, czy wtyczka nie została dodana do słownika
        plugins = self.plugin_manager.get_plugins()
        self.assertNotIn("invalid_plugin", plugins)
    
    def test_get_plugin(self):
        """
        Test pobierania danych wtyczki.
        """
        # Dane testowej wtyczki
        plugin_data = {
            "name": "get_test_plugin",
            "type": "local",
            "description": "Wtyczka do testu get_plugin",
            "status": "online"
        }
        
        # Rejestracja wtyczki
        self.plugin_manager.register_plugin(plugin_data)
        
        # Pobranie danych wtyczki
        plugin = self.plugin_manager.get_plugin("get_test_plugin")
        
        # Sprawdzenie, czy dane są poprawne
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin["name"], "get_test_plugin")
        self.assertEqual(plugin["type"], "local")
        self.assertEqual(plugin["description"], "Wtyczka do testu get_plugin")
        self.assertEqual(plugin["status"], "online")
    
    def test_get_nonexistent_plugin(self):
        """
        Test pobierania danych nieistniejącej wtyczki.
        """
        # Pobranie danych nieistniejącej wtyczki
        plugin = self.plugin_manager.get_plugin("nonexistent_plugin")
        
        # Sprawdzenie, czy zwrócono None
        self.assertIsNone(plugin)
    
    def test_unregister_plugin(self):
        """
        Test usuwania wtyczki.
        """
        # Dane testowej wtyczki
        plugin_data = {
            "name": "plugin_to_remove",
            "type": "local",
            "description": "Wtyczka do usunięcia",
            "status": "online"
        }
        
        # Rejestracja wtyczki
        self.plugin_manager.register_plugin(plugin_data)
        
        # Sprawdzenie, czy wtyczka została dodana
        self.assertIn("plugin_to_remove", self.plugin_manager.get_plugins())
        
        # Usunięcie wtyczki
        success = self.plugin_manager.unregister_plugin("plugin_to_remove")
        
        # Sprawdzenie, czy operacja się powiodła
        self.assertTrue(success)
        
        # Sprawdzenie, czy wtyczka została usunięta
        self.assertNotIn("plugin_to_remove", self.plugin_manager.get_plugins())
    
    def test_unregister_nonexistent_plugin(self):
        """
        Test usuwania nieistniejącej wtyczki.
        """
        # Próba usunięcia nieistniejącej wtyczki
        success = self.plugin_manager.unregister_plugin("nonexistent_plugin")
        
        # Sprawdzenie, czy operacja się nie powiodła
        self.assertFalse(success)
    
    def test_handle_plugin_announcement(self):
        """
        Test obsługi ogłoszenia wtyczki przez MQTT.
        """
        # Utworzenie mocka wiadomości MQTT
        message_mock = MagicMock()
        message_mock.topic = "plugin/announce"
        message_mock.payload = json.dumps({
            "name": "mqtt_plugin",
            "type": "mqtt",
            "description": "Wtyczka MQTT",
            "status": "online"
        }).encode('utf-8')
        
        # Wywołanie metody obsługi ogłoszenia
        self.plugin_manager._handle_plugin_announcement(None, None, message_mock)
        
        # Sprawdzenie, czy wtyczka została dodana
        plugins = self.plugin_manager.get_plugins()
        self.assertIn("mqtt_plugin", plugins)
        self.assertEqual(plugins["mqtt_plugin"]["type"], "mqtt")
        self.assertEqual(plugins["mqtt_plugin"]["description"], "Wtyczka MQTT")
        self.assertEqual(plugins["mqtt_plugin"]["status"], "online")
        self.assertIn("last_seen", plugins["mqtt_plugin"])
    
    def test_handle_invalid_announcement(self):
        """
        Test obsługi nieprawidłowego ogłoszenia wtyczki.
        """
        # Utworzenie mocka wiadomości MQTT z nieprawidłowym JSON
        message_mock = MagicMock()
        message_mock.topic = "plugin/announce"
        message_mock.payload = b"invalid json"
        
        # Wywołanie metody obsługi ogłoszenia
        self.plugin_manager._handle_plugin_announcement(None, None, message_mock)
        
        # Sprawdzenie, czy słownik wtyczek jest pusty
        self.assertEqual(len(self.plugin_manager.get_plugins()), 0)
        
        # Utworzenie mocka wiadomości MQTT z niepełnymi danymi
        message_mock.payload = json.dumps({
            "name": "incomplete_plugin",
            "type": "mqtt"
            # Brak pól 'description' i 'status'
        }).encode('utf-8')
        
        # Wywołanie metody obsługi ogłoszenia
        self.plugin_manager._handle_plugin_announcement(None, None, message_mock)
        
        # Sprawdzenie, czy słownik wtyczek jest nadal pusty
        self.assertEqual(len(self.plugin_manager.get_plugins()), 0)
    
    def test_status_monitor(self):
        """
        Test monitora statusu wtyczek.
        """
        # Dane testowej wtyczki
        plugin_data = {
            "name": "status_test_plugin",
            "type": "mqtt",
            "description": "Wtyczka do testu statusu",
            "status": "online",
            # Ustawienie last_seen na czas w przeszłości (przekraczający timeout)
            "last_seen": (datetime.now() - timedelta(seconds=2)).isoformat()
        }
        
        # Ręczne dodanie wtyczki do słownika
        with self.plugin_manager.lock:
            self.plugin_manager.plugins["status_test_plugin"] = plugin_data
            self.plugin_manager._save_plugins()
        
        # Wywołanie metody monitora statusu
        self.plugin_manager._start_status_monitor()
        
        # Odczekanie na zmianę statusu (timeout + margines)
        time.sleep(1.5)
        
        # Pobranie zaktualizowanych danych wtyczki
        plugin = self.plugin_manager.get_plugin("status_test_plugin")
        
        # Sprawdzenie, czy status został zmieniony na 'offline'
        self.assertEqual(plugin["status"], "offline")
    
    def test_mqtt_subscriptions(self):
        """
        Test konfiguracji subskrypcji MQTT.
        """
        # Utworzenie mocka dla klienta MQTT z odpowiednią konfiguracją
        mqtt_client_mock = MagicMock()
        mqtt_client_mock.config = {
            "topics": {
                "subscribe": ["plugin/announce"]
            }
        }
        mqtt_client_mock.client = MagicMock()
        mqtt_client_mock.connected = True
        
        # Utworzenie nowej instancji PluginManager z mockiem
        plugin_manager = PluginManager(
            mqtt_client=mqtt_client_mock,
            plugins_file=self.temp_file.name,
            offline_timeout=1
        )
        
        # Sprawdzenie, czy metoda message_callback_add została wywołana z odpowiednim tematem
        mqtt_client_mock.client.message_callback_add.assert_called_with(
            "plugin/announce", 
            plugin_manager._handle_plugin_announcement
        )
        
        # Sprawdzenie, czy metoda subscribe została wywołana
        mqtt_client_mock.client.subscribe.assert_called_with("plugin/announce")
    
if __name__ == '__main__':
    unittest.main()

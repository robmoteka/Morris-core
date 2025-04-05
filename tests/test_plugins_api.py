#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Testy jednostkowe dla API wtyczek.
"""

import unittest
import json
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

# Dodanie katalogu głównego do ścieżki, aby umożliwić importowanie modułów
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from plugins.manager import PluginManager
from api.plugins import plugins_bp

class PluginsApiTest(unittest.TestCase):
    """
    Testy jednostkowe dla API wtyczek.
    """
    
    def setUp(self):
        """
        Przygotowanie środowiska testowego przed każdym testem.
        """
        # Konfiguracja aplikacji testowej
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        
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
        
        # Dodanie Plugin Managera do kontekstu aplikacji
        app.config['plugin_manager'] = self.plugin_manager
        
        # Utworzenie klienta testowego
        self.client = app.test_client()
        
        # Kontekst aplikacji
        self.app_context = app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """
        Czyszczenie po każdym teście.
        """
        # Usunięcie tymczasowego pliku
        os.unlink(self.temp_file.name)
        
        # Usunięcie kontekstu aplikacji
        self.app_context.pop()
    
    def test_get_empty_plugins_list(self):
        """
        Test pobierania pustej listy wtyczek.
        """
        # Wysłanie żądania GET do endpointu /api/plugins
        response = self.client.get('/api/plugins')
        
        # Sprawdzenie kodu odpowiedzi
        self.assertEqual(response.status_code, 200)
        
        # Parsowanie odpowiedzi JSON
        data = json.loads(response.data)
        
        # Sprawdzenie struktury odpowiedzi
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['count'], 0)
        self.assertEqual(data['plugins'], {})
    
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
        
        # Wysłanie żądania POST do endpointu /api/plugins
        response = self.client.post(
            '/api/plugins',
            data=json.dumps(plugin_data),
            content_type='application/json'
        )
        
        # Sprawdzenie kodu odpowiedzi
        self.assertEqual(response.status_code, 201)
        
        # Parsowanie odpowiedzi JSON
        data = json.loads(response.data)
        
        # Sprawdzenie struktury odpowiedzi
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], 'Zarejestrowano wtyczkę: test_plugin')
        self.assertEqual(data['plugin']['name'], 'test_plugin')
        self.assertEqual(data['plugin']['type'], 'local')
        self.assertEqual(data['plugin']['description'], 'Testowa wtyczka')
        self.assertEqual(data['plugin']['status'], 'online')
    
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
        
        # Wysłanie żądania POST do endpointu /api/plugins
        response = self.client.post(
            '/api/plugins',
            data=json.dumps(plugin_data),
            content_type='application/json'
        )
        
        # Sprawdzenie kodu odpowiedzi
        self.assertEqual(response.status_code, 400)
        
        # Parsowanie odpowiedzi JSON
        data = json.loads(response.data)
        
        # Sprawdzenie struktury odpowiedzi
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Brakujące wymagane pola: status')
    
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
        
        # Wysłanie żądania GET do endpointu /api/plugins/<name>
        response = self.client.get('/api/plugins/get_test_plugin')
        
        # Sprawdzenie kodu odpowiedzi
        self.assertEqual(response.status_code, 200)
        
        # Parsowanie odpowiedzi JSON
        data = json.loads(response.data)
        
        # Sprawdzenie struktury odpowiedzi
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['plugin']['name'], 'get_test_plugin')
        self.assertEqual(data['plugin']['type'], 'local')
        self.assertEqual(data['plugin']['description'], 'Wtyczka do testu get_plugin')
        self.assertEqual(data['plugin']['status'], 'online')
    
    def test_get_nonexistent_plugin(self):
        """
        Test pobierania danych nieistniejącej wtyczki.
        """
        # Wysłanie żądania GET do endpointu /api/plugins/<name>
        response = self.client.get('/api/plugins/nonexistent_plugin')
        
        # Sprawdzenie kodu odpowiedzi
        self.assertEqual(response.status_code, 404)
        
        # Parsowanie odpowiedzi JSON
        data = json.loads(response.data)
        
        # Sprawdzenie struktury odpowiedzi
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Wtyczka nonexistent_plugin nie istnieje')
    
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
        
        # Wysłanie żądania DELETE do endpointu /api/plugins/<name>
        response = self.client.delete('/api/plugins/plugin_to_remove')
        
        # Sprawdzenie kodu odpowiedzi
        self.assertEqual(response.status_code, 200)
        
        # Parsowanie odpowiedzi JSON
        data = json.loads(response.data)
        
        # Sprawdzenie struktury odpowiedzi
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], 'Usunięto wtyczkę: plugin_to_remove')
        
        # Sprawdzenie, czy wtyczka została rzeczywiście usunięta
        self.assertIsNone(self.plugin_manager.get_plugin('plugin_to_remove'))
    
    def test_unregister_nonexistent_plugin(self):
        """
        Test usuwania nieistniejącej wtyczki.
        """
        # Wysłanie żądania DELETE do endpointu /api/plugins/<name>
        response = self.client.delete('/api/plugins/nonexistent_plugin')
        
        # Sprawdzenie kodu odpowiedzi
        self.assertEqual(response.status_code, 404)
        
        # Parsowanie odpowiedzi JSON
        data = json.loads(response.data)
        
        # Sprawdzenie struktury odpowiedzi
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Nie udało się usunąć wtyczki nonexistent_plugin')

if __name__ == '__main__':
    unittest.main()

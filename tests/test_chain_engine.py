#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Testy jednostkowe dla modułu Chain Engine.
"""

import unittest
import json
import os
import tempfile
from unittest.mock import MagicMock, patch
import sys
import logging

# Dodanie katalogu głównego do ścieżki, aby umożliwić importowanie modułów
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.chain_engine import ChainEngine
from plugins.base import BasePlugin

# Wyłączenie logowania podczas testów
logging.disable(logging.CRITICAL)

class TestPlugin(BasePlugin):
    """
    Testowa wtyczka do użycia w testach.
    """
    def process(self, data, params=None):
        """
        Przykładowa implementacja metody process.
        Dodaje prefix 'test_' do wszystkich wartości tekstowych.
        """
        if not isinstance(data, dict):
            return data
            
        result = data.copy()
        for key, value in result.items():
            if isinstance(value, str):
                result[key] = f"test_{value}"
        
        return result

class ErrorPlugin(BasePlugin):
    """
    Testowa wtyczka, która zawsze zgłasza wyjątek.
    """
    def process(self, data, params=None):
        """
        Zgłasza wyjątek podczas przetwarzania.
        """
        raise ValueError("Testowy błąd wtyczki")

class ChainEngineTest(unittest.TestCase):
    """
    Testy jednostkowe dla klasy ChainEngine.
    """
    
    def setUp(self):
        """
        Przygotowanie środowiska testowego przed każdym testem.
        """
        # Utworzenie tymczasowego pliku z definicjami chainów
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        
        # Przykładowe definicje chainów do testów
        self.test_chains = {
            "test_chain": {
                "trigger": "webhook:test",
                "description": "Chain testowy",
                "steps": [
                    {
                        "plugin": "TestPlugin",
                        "params": {"param1": "value1"}
                    },
                    {
                        "plugin": "TestPlugin",
                        "params": {"param2": "value2"}
                    }
                ]
            },
            "error_chain": {
                "trigger": "webhook:error",
                "description": "Chain z błędem",
                "steps": [
                    {
                        "plugin": "ErrorPlugin"
                    }
                ]
            },
            "remote_chain": {
                "trigger": "mqtt:test",
                "description": "Chain z zdalną wtyczką",
                "steps": [
                    {
                        "plugin": "remote:device1:TestPlugin",
                        "params": {"timeout": 2}
                    }
                ]
            }
        }
        
        # Zapisanie definicji chainów do tymczasowego pliku
        with open(self.temp_file.name, 'w') as f:
            json.dump(self.test_chains, f)
        
        # Utworzenie mocka dla klienta MQTT
        self.mqtt_client_mock = MagicMock()
        
        # Utworzenie instancji ChainEngine do testów
        self.chain_engine = ChainEngine(
            mqtt_client=self.mqtt_client_mock,
            chains_file=self.temp_file.name
        )
        
        # Podmiana metody importowania modułów, aby używać naszych testowych wtyczek
        self.original_import_module = __import__
        
        def mock_import_module(name, *args, **kwargs):
            if name == "plugins.test_plugin":
                # Tworzenie mocka modułu z naszą testową wtyczką
                module_mock = MagicMock()
                module_mock.TestPlugin = TestPlugin
                return module_mock
            elif name == "plugins.error_plugin":
                # Tworzenie mocka modułu z naszą błędną wtyczką
                module_mock = MagicMock()
                module_mock.ErrorPlugin = ErrorPlugin
                return module_mock
            else:
                # Dla innych modułów używamy standardowego importu
                return self.original_import_module(name, *args, **kwargs)
        
        # Podmieniamy funkcję importlib.import_module na naszą funkcję mock_import_module
        self.import_module_patcher = patch('importlib.import_module', side_effect=mock_import_module)
        self.import_module_mock = self.import_module_patcher.start()
    
    def tearDown(self):
        """
        Czyszczenie po każdym teście.
        """
        # Usunięcie tymczasowego pliku
        os.unlink(self.temp_file.name)
        
        # Zatrzymanie patchera
        self.import_module_patcher.stop()
    
    def test_load_chains(self):
        """
        Test wczytywania chainów z pliku.
        """
        # Sprawdzenie, czy chainy zostały poprawnie wczytane
        self.assertEqual(len(self.chain_engine.chains), 3)
        self.assertIn("test_chain", self.chain_engine.chains)
        self.assertIn("error_chain", self.chain_engine.chains)
        self.assertIn("remote_chain", self.chain_engine.chains)
    
    def test_validate_chain(self):
        """
        Test walidacji definicji chaina.
        """
        # Poprawna definicja
        valid_chain = {
            "trigger": "webhook:test",
            "steps": [
                {"plugin": "TestPlugin"}
            ]
        }
        self.assertTrue(self.chain_engine._validate_chain(valid_chain))
        
        # Niepoprawne definicje
        invalid_chain1 = {
            "steps": [
                {"plugin": "TestPlugin"}
            ]
        }  # Brak triggera
        self.assertFalse(self.chain_engine._validate_chain(invalid_chain1))
        
        invalid_chain2 = {
            "trigger": "webhook:test"
        }  # Brak kroków
        self.assertFalse(self.chain_engine._validate_chain(invalid_chain2))
        
        invalid_chain3 = {
            "trigger": "webhook:test",
            "steps": [
                {"not_plugin": "TestPlugin"}
            ]
        }  # Brak pluginu w kroku
        self.assertFalse(self.chain_engine._validate_chain(invalid_chain3))
    
    def test_get_chain_for_trigger(self):
        """
        Test znajdowania chaina na podstawie triggera.
        """
        # Istniejący trigger
        chain_id, chain = self.chain_engine.get_chain_for_trigger("webhook:test")
        self.assertEqual(chain_id, "test_chain")
        self.assertEqual(chain["description"], "Chain testowy")
        
        # Nieistniejący trigger
        chain_id, chain = self.chain_engine.get_chain_for_trigger("webhook:nonexistent")
        self.assertIsNone(chain_id)
        self.assertIsNone(chain)
    
    def test_add_and_remove_chain(self):
        """
        Test dodawania i usuwania chainów.
        """
        # Dodanie nowego chaina
        new_chain = {
            "trigger": "webhook:new",
            "description": "Nowy chain",
            "steps": [
                {"plugin": "TestPlugin"}
            ]
        }
        self.assertTrue(self.chain_engine.add_chain("new_chain", new_chain))
        self.assertIn("new_chain", self.chain_engine.chains)
        
        # Usunięcie chaina
        self.assertTrue(self.chain_engine.remove_chain("new_chain"))
        self.assertNotIn("new_chain", self.chain_engine.chains)
        
        # Próba usunięcia nieistniejącego chaina
        self.assertFalse(self.chain_engine.remove_chain("nonexistent_chain"))
    
    def test_run_chain(self):
        """
        Test uruchamiania chaina.
        """
        # Uruchomienie poprawnego chaina
        input_data = {"message": "hello", "value": 42}
        result = self.chain_engine.run_chain("webhook:test", input_data)
        
        # Sprawdzenie, czy dane zostały przetworzone przez obie wtyczki
        self.assertEqual(result["message"], "test_test_hello")
        self.assertEqual(result["value"], 42)  # Wartość liczbowa nie powinna być zmieniona
    
    def test_run_nonexistent_chain(self):
        """
        Test uruchamiania nieistniejącego chaina.
        """
        input_data = {"message": "hello"}
        result = self.chain_engine.run_chain("webhook:nonexistent", input_data)
        
        # Dane powinny być zwrócone bez zmian
        self.assertEqual(result, input_data)
    
    def test_run_chain_with_error(self):
        """
        Test uruchamiania chaina, który zgłasza błąd.
        """
        input_data = {"message": "hello"}
        result = self.chain_engine.run_chain("webhook:error", input_data)
        
        # Mimo błędu, chain powinien kontynuować działanie i zwrócić dane wejściowe
        self.assertEqual(result, input_data)
    
    @patch('threading.Thread')
    def test_run_chain_async(self, thread_mock):
        """
        Test asynchronicznego uruchamiania chaina.
        """
        input_data = {"message": "hello"}
        callback = MagicMock()
        
        self.chain_engine.run_chain_async("webhook:test", input_data, callback)
        
        # Sprawdzenie, czy utworzono wątek
        thread_mock.assert_called_once()
        
        # Sprawdzenie, czy wątek został uruchomiony
        thread_instance = thread_mock.return_value
        thread_instance.start.assert_called_once()
    
    def test_run_local_plugin(self):
        """
        Test uruchamiania lokalnej wtyczki.
        """
        input_data = {"message": "hello"}
        result = self.chain_engine._run_local_plugin("TestPlugin", input_data, {})
        
        # Sprawdzenie, czy dane zostały przetworzone przez wtyczkę
        self.assertEqual(result["message"], "test_hello")
    
    def test_run_local_plugin_error(self):
        """
        Test uruchamiania lokalnej wtyczki, która zgłasza błąd.
        """
        input_data = {"message": "hello"}
        result = self.chain_engine._run_local_plugin("ErrorPlugin", input_data, {})
        
        # W przypadku błędu, wtyczka powinna zwrócić dane wejściowe bez zmian
        self.assertEqual(result, input_data)
    
    def test_run_remote_plugin(self):
        """
        Test uruchamiania zdalnej wtyczki.
        """
        input_data = {"message": "hello"}
        
        # Uruchomienie zdalnej wtyczki
        result = self.chain_engine._run_remote_plugin("remote:device1:TestPlugin", input_data, {"timeout": 2})
        
        # Sprawdzenie, czy dane zostały opublikowane przez MQTT
        self.mqtt_client_mock.publish.assert_called_once()
        
        # Zdalna wtyczka powinna zwrócić dane wejściowe (w obecnej implementacji)
        self.assertEqual(result, input_data)
    
    def test_run_remote_plugin_no_mqtt(self):
        """
        Test uruchamiania zdalnej wtyczki bez klienta MQTT.
        """
        # Utworzenie instancji ChainEngine bez klienta MQTT
        chain_engine_no_mqtt = ChainEngine(mqtt_client=None, chains_file=self.temp_file.name)
        
        input_data = {"message": "hello"}
        result = chain_engine_no_mqtt._run_remote_plugin("remote:device1:TestPlugin", input_data, {})
        
        # Bez klienta MQTT, wtyczka powinna zwrócić dane wejściowe bez zmian
        self.assertEqual(result, input_data)
    
    def test_handle_plugin_response(self):
        """
        Test obsługi odpowiedzi od zdalnej wtyczki.
        """
        # Utworzenie mocka wiadomości MQTT
        msg_mock = MagicMock()
        msg_mock.topic = "plugin/device1/output"
        msg_mock.payload = json.dumps({"data": {"message": "processed"}}).encode()
        
        # Dodanie kolejki dla odpowiedzi
        from queue import Queue
        response_queue = Queue()
        self.chain_engine.response_queues["plugin/device1"] = response_queue
        
        # Wywołanie metody obsługi odpowiedzi
        self.chain_engine._handle_plugin_response(msg_mock)
        
        # Sprawdzenie, czy odpowiedź została dodana do kolejki
        self.assertFalse(response_queue.empty())
        response = response_queue.get()
        self.assertEqual(response["data"]["message"], "processed")
        
        # Sprawdzenie, czy odpowiedź została zapisana w słowniku
        self.assertIn("plugin/device1", self.chain_engine.remote_responses)
        self.assertEqual(self.chain_engine.remote_responses["plugin/device1"]["data"]["message"], "processed")

if __name__ == '__main__':
    unittest.main()

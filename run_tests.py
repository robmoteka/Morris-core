#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Skrypt do uruchamiania wszystkich testów dla systemu Morris Core.
"""

import unittest
import sys
import os

# Dodanie katalogu głównego do ścieżki, aby umożliwić importowanie modułów
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Importowanie testów
from tests.test_plugins_api import PluginsApiTest
from tests.test_plugin_manager import PluginManagerTest
from tests.test_plugin_manager_mqtt_integration import PluginManagerMqttIntegrationTest

def run_all_tests():
    """
    Uruchamia wszystkie testy jednostkowe i integracyjne.
    """
    # Utworzenie loadera testów
    loader = unittest.TestLoader()
    
    # Utworzenie suite testów
    test_suite = unittest.TestSuite()
    
    # Dodanie testów do suite
    test_suite.addTest(loader.loadTestsFromTestCase(PluginsApiTest))
    test_suite.addTest(loader.loadTestsFromTestCase(PluginManagerTest))
    test_suite.addTest(loader.loadTestsFromTestCase(PluginManagerMqttIntegrationTest))
    
    # Utworzenie runnera testów
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Uruchomienie testów
    result = runner.run(test_suite)
    
    # Zwrócenie kodu wyjścia (0 jeśli wszystkie testy przeszły, 1 w przeciwnym razie)
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    # Uruchomienie testów i zwrócenie kodu wyjścia
    sys.exit(run_all_tests())

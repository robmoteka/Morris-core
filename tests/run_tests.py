#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Skrypt do uruchamiania wszystkich testów jednostkowych dla projektu Morris.
Automatycznie wykrywa i uruchamia wszystkie testy w katalogu tests.
"""

import unittest
import sys
import os

# Dodanie katalogu głównego projektu do ścieżki, aby umożliwić import modułów
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_all_tests():
    """
    Funkcja wykrywająca i uruchamiająca wszystkie testy jednostkowe.
    
    Returns:
        bool: True jeśli wszystkie testy zakończyły się sukcesem, False w przeciwnym wypadku
    """
    # Wykrycie wszystkich testów w bieżącym katalogu
    testLoader = unittest.TestLoader()
    testSuite = testLoader.discover(start_dir=os.path.dirname(__file__), pattern='test_*.py')
    
    # Uruchomienie testów
    testRunner = unittest.TextTestRunner(verbosity=2)
    result = testRunner.run(testSuite)
    
    # Wyświetlenie podsumowania
    print("\n=== Podsumowanie testów ===")
    print(f"Liczba testów: {result.testsRun}")
    print(f"Błędy: {len(result.errors)}")
    print(f"Niepowodzenia: {len(result.failures)}")
    
    # Zwrócenie informacji o sukcesie lub porażce
    return len(result.errors) == 0 and len(result.failures) == 0

if __name__ == '__main__':
    # Uruchomienie testów i ustawienie kodu wyjścia
    success = run_all_tests()
    sys.exit(0 if success else 1)

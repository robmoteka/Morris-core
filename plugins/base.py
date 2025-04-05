#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moduł zawierający klasę bazową dla wtyczek (plugins) w systemie Morris.
Wszystkie wtyczki powinny dziedziczyć po klasie BasePlugin.
"""

import logging
from abc import ABC, abstractmethod

# Konfiguracja loggera
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BasePlugin(ABC):
    """
    Klasa bazowa dla wszystkich wtyczek (plugins) w systemie Morris.
    Definiuje interfejs, który muszą implementować wszystkie wtyczki.
    """
    
    def __init__(self, config=None):
        """
        Inicjalizacja wtyczki.
        
        Args:
            config (dict, optional): Konfiguracja wtyczki. Domyślnie None.
        """
        self.name = self.__class__.__name__
        self.config = config or {}
        logger.info(f"Zainicjalizowano wtyczkę: {self.name}")
    
    @abstractmethod
    def process(self, data, params=None):
        """
        Metoda abstrakcyjna, którą muszą implementować wszystkie wtyczki.
        Przetwarza dane wejściowe i zwraca wynik.
        
        Args:
            data (dict): Dane wejściowe do przetworzenia.
            params (dict, optional): Dodatkowe parametry dla przetwarzania. Domyślnie None.
            
        Returns:
            dict: Przetworzone dane.
        """
        pass
    
    def validate_input(self, data):
        """
        Walidacja danych wejściowych.
        Metoda pomocnicza, którą mogą nadpisać wtyczki.
        
        Args:
            data (dict): Dane wejściowe do walidacji.
            
        Returns:
            bool: True jeśli dane są poprawne, False w przeciwnym wypadku.
        """
        return isinstance(data, dict)
    
    def log_processing(self, data, result):
        """
        Logowanie informacji o przetwarzaniu danych.
        
        Args:
            data (dict): Dane wejściowe.
            result (dict): Wynik przetwarzania.
        """
        logger.debug(f"Wtyczka {self.name} przetworzyła dane: {data} -> {result}")

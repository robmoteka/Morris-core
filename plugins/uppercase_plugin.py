#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Przykładowa wtyczka UppercasePlugin do systemu Morris.
Konwertuje wartości tekstowe w danych wejściowych na wielkie litery.
"""

import logging
from plugins.base import BasePlugin

# Konfiguracja loggera
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UppercasePlugin(BasePlugin):
    """
    Wtyczka UppercasePlugin.
    Konwertuje wartości tekstowe w danych wejściowych na wielkie litery.
    """
    
    def process(self, data, params=None):
        """
        Przetwarza dane wejściowe, konwertując wartości tekstowe na wielkie litery.
        
        Args:
            data (dict): Dane wejściowe do przetworzenia.
            params (dict, optional): Dodatkowe parametry dla przetwarzania.
                                    Może zawierać 'keys' - listę kluczy do przetworzenia.
                                    Jeśli nie podano, wszystkie wartości tekstowe zostaną przekonwertowane.
                                    Domyślnie None.
            
        Returns:
            dict: Przetworzone dane z wartościami tekstowymi zamienionymi na wielkie litery.
        """
        if not self.validate_input(data):
            logger.error("Nieprawidłowy format danych wejściowych")
            return data
        
        params = params or {}
        specific_keys = params.get('keys', None)
        
        result = data.copy()  # Tworzymy kopię, aby nie modyfikować oryginalnych danych
        
        # Jeśli podano konkretne klucze, przetwarzamy tylko je
        if specific_keys:
            for key in specific_keys:
                if key in result and isinstance(result[key], str):
                    result[key] = result[key].upper()
        # W przeciwnym razie przetwarzamy wszystkie wartości tekstowe
        else:
            for key, value in result.items():
                if isinstance(value, str):
                    result[key] = value.upper()
        
        # Logowanie informacji o przetworzeniu
        self.log_processing(data, result)
        
        return result

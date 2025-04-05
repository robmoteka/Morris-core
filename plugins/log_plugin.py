#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Przykładowa wtyczka LogPlugin do systemu Morris.
Loguje otrzymane dane i przekazuje je dalej bez zmian.
"""

import logging
from plugins.base import BasePlugin

# Konfiguracja loggera
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LogPlugin(BasePlugin):
    """
    Wtyczka LogPlugin.
    Loguje otrzymane dane i przekazuje je dalej bez zmian.
    """
    
    def process(self, data, params=None):
        """
        Loguje otrzymane dane i przekazuje je dalej bez zmian.
        
        Args:
            data (dict): Dane wejściowe do przetworzenia.
            params (dict, optional): Dodatkowe parametry dla przetwarzania. 
                                    Może zawierać 'log_level' do określenia poziomu logowania.
                                    Domyślnie None.
            
        Returns:
            dict: Te same dane, które zostały przekazane na wejściu.
        """
        params = params or {}
        log_level = params.get('log_level', 'info').lower()
        
        # Wybór odpowiedniej metody logowania
        if log_level == 'debug':
            logger.debug(f"LogPlugin otrzymał dane: {data}")
        elif log_level == 'warning':
            logger.warning(f"LogPlugin otrzymał dane: {data}")
        elif log_level == 'error':
            logger.error(f"LogPlugin otrzymał dane: {data}")
        else:  # domyślnie 'info'
            logger.info(f"LogPlugin otrzymał dane: {data}")
        
        # Logowanie dodatkowych informacji, jeśli określono w parametrach
        if params.get('log_details', False):
            logger.info(f"Szczegóły danych: {len(data)} elementów")
            for key, value in data.items():
                logger.info(f"  - {key}: {value}")
        
        # Zwracamy te same dane bez zmian
        return data

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moduł Plugin Manager dla systemu Morris.
Odpowiada za zarządzanie wtyczkami (lokalnymi i zdalnymi), ich rejestracją,
śledzeniem statusów oraz dostarczaniem API do odpytywania dostępnych wtyczek.
"""

import json
import os
import logging
import threading
import time
from datetime import datetime

# Konfiguracja loggera
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PluginManager:
    """
    Klasa zarządzająca wtyczkami w systemie Morris.
    
    Odpowiada za:
    - Rejestrację wtyczek (lokalnych i zdalnych)
    - Przechowywanie metadanych (nazwa, typ, opis, status)
    - Obsługę statusów wtyczek (online/offline)
    - Dostarczanie API do odpytywania dostępnych wtyczek
    - Odbiór ogłoszeń wtyczek przez MQTT (topic plugin/announce)
    """
    
    def __init__(self, mqtt_client=None, plugins_file="data/plugins.json", offline_timeout=60):
        """
        Inicjalizacja managera wtyczek.
        
        Args:
            mqtt_client: Klient MQTT do komunikacji z zewnętrznymi wtyczkami
            plugins_file (str): Ścieżka do pliku z danymi wtyczek
            offline_timeout (int): Czas w sekundach, po którym wtyczka jest oznaczana jako offline
        """
        self.mqtt_client = mqtt_client
        self.plugins_file = plugins_file
        self.offline_timeout = offline_timeout
        self.plugins = {}
        self.lock = threading.Lock()  # Blokada do bezpiecznego dostępu do słownika wtyczek
        
        # Utworzenie katalogu dla pliku plugins.json, jeśli nie istnieje
        os.makedirs(os.path.dirname(self.plugins_file), exist_ok=True)
        
        # Wczytanie wtyczek z pliku
        self._load_plugins()
        
        # Konfiguracja subskrypcji MQTT
        if self.mqtt_client:
            self._setup_mqtt_subscriptions()
            
        # Uruchomienie wątku monitorującego status wtyczek
        self._start_status_monitor()
    
    def _load_plugins(self):
        """
        Wczytuje dane wtyczek z pliku JSON.
        Jeśli plik nie istnieje, tworzy pusty słownik wtyczek.
        """
        try:
            if os.path.exists(self.plugins_file):
                with open(self.plugins_file, 'r', encoding='utf-8') as file:
                    self.plugins = json.load(file)
                logger.info(f"Wczytano {len(self.plugins)} wtyczek z pliku {self.plugins_file}")
            else:
                logger.info(f"Plik {self.plugins_file} nie istnieje. Tworzenie pustego słownika wtyczek.")
                self.plugins = {}
                self._save_plugins()
        except Exception as e:
            logger.error(f"Błąd podczas wczytywania wtyczek z pliku: {e}")
            self.plugins = {}
    
    def _save_plugins(self):
        """
        Zapisuje dane wtyczek do pliku JSON.
        """
        try:
            with open(self.plugins_file, 'w', encoding='utf-8') as file:
                json.dump(self.plugins, file, indent=2, ensure_ascii=False)
            logger.info(f"Zapisano {len(self.plugins)} wtyczek do pliku {self.plugins_file}")
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania wtyczek do pliku: {e}")
    
    def _setup_mqtt_subscriptions(self):
        """
        Konfiguruje subskrypcje MQTT dla ogłoszeń wtyczek.
        """
        if not self.mqtt_client:
            logger.warning("Klient MQTT nie jest dostępny. Nie można skonfigurować subskrypcji.")
            return
        
        # Dodanie tematu plugin/announce do listy subskrybowanych tematów w kliencie MQTT
        if "topics" in self.mqtt_client.config and "subscribe" in self.mqtt_client.config["topics"]:
            if "plugin/announce" not in self.mqtt_client.config["topics"]["subscribe"]:
                self.mqtt_client.config["topics"]["subscribe"].append("plugin/announce")
        
        # Jeśli klient MQTT ma już zainicjalizowany obiekt client, dodajemy callback
        if hasattr(self.mqtt_client, 'client') and self.mqtt_client.client:
            # Dodanie callbacka dla wiadomości
            self.mqtt_client.client.message_callback_add("plugin/announce", self._handle_plugin_announcement)
            
            # Jeśli klient jest już połączony, dodajemy subskrypcję bezpośrednio
            if self.mqtt_client.connected:
                self.mqtt_client.client.subscribe("plugin/announce")
        
        logger.info("Skonfigurowano subskrypcje MQTT dla ogłoszeń wtyczek")
    
    def _handle_plugin_announcement(self, client, userdata, message):
        """
        Obsługuje ogłoszenia wtyczek przychodzące przez MQTT.
        
        Args:
            client: Klient MQTT
            userdata: Dane użytkownika
            message: Wiadomość MQTT
        """
        try:
            # Dekodowanie wiadomości JSON
            payload = json.loads(message.payload.decode('utf-8'))
            
            # Sprawdzenie wymaganych pól
            if not all(key in payload for key in ['name', 'type', 'description', 'status']):
                logger.warning(f"Otrzymano nieprawidłowe ogłoszenie wtyczki: {payload}")
                return
            
            plugin_name = payload['name']
            
            # Dodanie znacznika czasowego
            payload['last_seen'] = datetime.now().isoformat()
            
            # Aktualizacja lub dodanie wtyczki
            with self.lock:
                self.plugins[plugin_name] = payload
                self._save_plugins()
            
            logger.info(f"Zarejestrowano/zaktualizowano wtyczkę: {plugin_name}")
            
        except json.JSONDecodeError:
            logger.error(f"Otrzymano nieprawidłowy format JSON: {message.payload}")
        except Exception as e:
            logger.error(f"Błąd podczas przetwarzania ogłoszenia wtyczki: {e}")
    
    def _start_status_monitor(self):
        """
        Uruchamia wątek monitorujący status wtyczek.
        Sprawdza, czy wtyczki są aktywne i aktualizuje ich status.
        """
        def monitor_plugins():
            while True:
                try:
                    current_time = datetime.now()
                    plugins_to_update = []
                    
                    with self.lock:
                        for name, plugin in self.plugins.items():
                            # Sprawdzenie, czy wtyczka ma znacznik czasowy
                            if 'last_seen' in plugin and plugin['status'] == 'online':
                                last_seen = datetime.fromisoformat(plugin['last_seen'])
                                time_diff = (current_time - last_seen).total_seconds()
                                
                                # Jeśli przekroczono timeout, oznacz jako offline
                                if time_diff > self.offline_timeout:
                                    plugin['status'] = 'offline'
                                    plugins_to_update.append(name)
                                    logger.info(f"Wtyczka {name} oznaczona jako offline (ostatnio widziana {time_diff:.1f}s temu)")
                    
                    # Jeśli są wtyczki do aktualizacji, zapisz zmiany
                    if plugins_to_update:
                        self._save_plugins()
                
                except Exception as e:
                    logger.error(f"Błąd w monitorze statusu wtyczek: {e}")
                
                # Sprawdzanie co 10 sekund
                time.sleep(10)
        
        # Uruchomienie wątku monitorującego
        monitor_thread = threading.Thread(target=monitor_plugins, daemon=True)
        monitor_thread.start()
        logger.info("Uruchomiono monitor statusu wtyczek")
    
    def get_plugins(self):
        """
        Zwraca listę wszystkich zarejestrowanych wtyczek.
        
        Returns:
            dict: Słownik z danymi wszystkich wtyczek
        """
        with self.lock:
            return self.plugins.copy()
    
    def get_plugin(self, name):
        """
        Zwraca dane konkretnej wtyczki.
        
        Args:
            name (str): Nazwa wtyczki
            
        Returns:
            dict: Dane wtyczki lub None, jeśli wtyczka nie istnieje
        """
        with self.lock:
            return self.plugins.get(name)
    
    def register_plugin(self, plugin_data):
        """
        Rejestruje nową wtyczkę lub aktualizuje istniejącą.
        
        Args:
            plugin_data (dict): Dane wtyczki (name, type, description, status)
            
        Returns:
            bool: True, jeśli operacja się powiodła, False w przeciwnym wypadku
        """
        try:
            # Sprawdzenie wymaganych pól
            if not all(key in plugin_data for key in ['name', 'type', 'description', 'status']):
                logger.warning(f"Próba rejestracji wtyczki z niepełnymi danymi: {plugin_data}")
                return False
            
            plugin_name = plugin_data['name']
            
            # Dodanie znacznika czasowego
            plugin_data['last_seen'] = datetime.now().isoformat()
            
            # Aktualizacja lub dodanie wtyczki
            with self.lock:
                self.plugins[plugin_name] = plugin_data
                self._save_plugins()
            
            logger.info(f"Ręcznie zarejestrowano/zaktualizowano wtyczkę: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Błąd podczas rejestracji wtyczki: {e}")
            return False
    
    def unregister_plugin(self, name):
        """
        Usuwa wtyczkę z rejestru.
        
        Args:
            name (str): Nazwa wtyczki do usunięcia
            
        Returns:
            bool: True, jeśli operacja się powiodła, False w przeciwnym wypadku
        """
        try:
            with self.lock:
                if name in self.plugins:
                    del self.plugins[name]
                    self._save_plugins()
                    logger.info(f"Usunięto wtyczkę: {name}")
                    return True
                else:
                    logger.warning(f"Próba usunięcia nieistniejącej wtyczki: {name}")
                    return False
        except Exception as e:
            logger.error(f"Błąd podczas usuwania wtyczki: {e}")
            return False

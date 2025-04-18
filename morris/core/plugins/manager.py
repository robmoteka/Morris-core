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

    def __init__(self, app=None):
        """
        Inicjalizacja managera wtyczek.

        Args:
            app: Instancja aplikacji Flask z konfiguracją
        """
        self.app = app
        self.mqtt_client = None
        self.plugins_file = app.config["PLUGINS_FILE"] if app else "data/plugins.json"
        self.offline_timeout = 60
        self.plugins = {}
        self.lock = (
            threading.Lock()
        )  # Blokada do bezpiecznego dostępu do słownika wtyczek

        # Utworzenie katalogu dla pliku plugins.json, jeśli nie istnieje
        os.makedirs(os.path.dirname(self.plugins_file), exist_ok=True)

        # Wczytanie wtyczek z pliku
        self._load_plugins()

        # Naprawienie statusów wtyczek lokalnych
        self.fix_plugin_statuses()

        # Uruchomienie wątku monitorującego status wtyczek
        self._start_status_monitor()

        # Konfiguracja MQTT zostanie wykonana później, gdy klient MQTT będzie dostępny
        logger.info("Zainicjalizowano PluginManager")

    def set_mqtt_client(self, mqtt_client):
        """
        Ustawia klienta MQTT dla managera wtyczek.

        Args:
            mqtt_client: Klient MQTT do komunikacji z zewnętrznymi wtyczkami
        """
        self.mqtt_client = mqtt_client
        self._setup_mqtt_subscriptions()

    def _load_plugins(self):
        """
        Wczytuje dane wtyczek z pliku JSON.
        Jeśli plik nie istnieje, tworzy pusty słownik wtyczek.
        """
        try:
            if os.path.exists(self.plugins_file):
                with open(self.plugins_file, "r", encoding="utf-8") as file:
                    self.plugins = json.load(file)
                logger.info(
                    f"Wczytano {len(self.plugins)} wtyczek z pliku {self.plugins_file}"
                )
            else:
                logger.info(
                    f"Plik {self.plugins_file} nie istnieje. Tworzenie pustego słownika wtyczek."
                )
                self.plugins = {}
                self._save_plugins()
        except Exception as e:
            logger.error(f"Błąd podczas wczytywania wtyczek z pliku: {e}")
            self.plugins = {}

    def fix_plugin_statuses(self):
        """
        Naprawia statusy istniejących wtyczek w pliku JSON.
        Ustawia status 'active' dla wszystkich wtyczek lokalnych.
        Usuwa pole 'last_seen' z wtyczek lokalnych.

        Returns:
            bool: True, jeśli wprowadzono zmiany, False w przeciwnym wypadku
        """
        updated = False
        with self.lock:
            for name, plugin in self.plugins.items():
                if plugin.get("type") == "local":
                    if plugin.get("status") != "active":
                        plugin["status"] = "active"
                        updated = True
                        logger.info(f"Naprawiono status wtyczki lokalnej: {name}")

                    # Usunięcie znacznika last_seen aby wtyczka nie była monitorowana
                    if "last_seen" in plugin:
                        del plugin["last_seen"]
                        updated = True

        # Jeśli wprowadzono zmiany, zapisz je
        if updated:
            self._save_plugins()
            logger.info("Zaktualizowano statusy wtyczek lokalnych")
        return updated

    def _save_plugins(self):
        """
        Zapisuje dane wtyczek do pliku JSON.
        """
        try:
            with open(self.plugins_file, "w", encoding="utf-8") as file:
                json.dump(self.plugins, file, indent=2, ensure_ascii=False)
            logger.info(
                f"Zapisano {len(self.plugins)} wtyczek do pliku {self.plugins_file}"
            )
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania wtyczek do pliku: {e}")

    def _setup_mqtt_subscriptions(self):
        """
        Konfiguruje subskrypcje MQTT dla ogłoszeń wtyczek.
        """
        if not self.mqtt_client:
            logger.warning(
                "Klient MQTT nie jest dostępny. Nie można skonfigurować subskrypcji."
            )
            return

        # Dodanie tematu plugin/announce do listy subskrybowanych tematów w kliencie MQTT
        if (
            "topics" in self.mqtt_client.config
            and "subscribe" in self.mqtt_client.config["topics"]
        ):
            if "plugin/announce" not in self.mqtt_client.config["topics"]["subscribe"]:
                self.mqtt_client.config["topics"]["subscribe"].append("plugin/announce")

        # Jeśli klient MQTT ma już zainicjalizowany obiekt client, dodajemy callback
        if hasattr(self.mqtt_client, "client") and self.mqtt_client.client:
            # Dodanie callbacka dla wiadomości
            self.mqtt_client.client.message_callback_add(
                "plugin/announce", self._handle_plugin_announcement
            )

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
            payload = json.loads(message.payload.decode("utf-8"))

            # Sprawdzenie wymaganych pól
            if not all(
                key in payload for key in ["name", "type", "description", "status"]
            ):
                logger.warning(f"Otrzymano nieprawidłowe ogłoszenie wtyczki: {payload}")
                return

            plugin_name = payload["name"]

            # Dodanie znacznika czasowego
            payload["last_seen"] = datetime.now().isoformat()

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
                            # Pomijamy wtyczki lokalne - nie podlegają monitorowaniu online/offline
                            if plugin.get("type") == "local":
                                continue

                            # Sprawdzenie, czy wtyczka ma znacznik czasowy
                            if "last_seen" in plugin and plugin["status"] == "online":
                                last_seen = datetime.fromisoformat(plugin["last_seen"])
                                time_diff = (current_time - last_seen).total_seconds()

                                # Jeśli przekroczono timeout, oznacz jako offline
                                if time_diff > self.offline_timeout:
                                    plugin["status"] = "offline"
                                    plugins_to_update.append(name)
                                    logger.info(
                                        f"Wtyczka {name} oznaczona jako offline (ostatnio widziana {time_diff:.1f}s temu)"
                                    )

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
            if not all(
                key in plugin_data for key in ["name", "type", "description", "status"]
            ):
                logger.warning(
                    f"Próba rejestracji wtyczki z niepełnymi danymi: {plugin_data}"
                )
                return False

            plugin_name = plugin_data["name"]

            # Rozróżnienie między wtyczkami lokalnymi i zdalnymi
            if plugin_data["type"] == "local":
                # Wtyczki lokalne zawsze mają status 'active' i nie podlegają monitorowaniu online/offline
                plugin_data["status"] = "active"
                # Usunięcie last_seen jeśli istnieje, aby wtyczka nie była monitorowana
                if "last_seen" in plugin_data:
                    del plugin_data["last_seen"]
            else:
                # Tylko dla wtyczek zdalnych dodajemy znacznik czasowy
                plugin_data["last_seen"] = datetime.now().isoformat()

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

    def update_plugin_status(self, plugin_id, status, timestamp, details=None):
        """
        Aktualizuje status wtyczki.

        Args:
            plugin_id (str): Identyfikator wtyczki
            status (str): Nowy status (online, offline, error, working)
            timestamp (str): Czas aktualizacji w formacie ISO
            details (dict, optional): Dodatkowe szczegóły statusu
        """
        with self.lock:
            if plugin_id not in self.plugins:
                logger.warning(
                    f"Próba aktualizacji statusu niezarejestrowanej wtyczki: {plugin_id}"
                )
                return False

            plugin = self.plugins[plugin_id]
            plugin["status"] = status
            plugin["last_seen"] = timestamp
            if details is not None:
                plugin["details"] = details

            self._save_plugins()
            logger.info(f"Zaktualizowano status wtyczki {plugin_id}: {status}")
            return True

    def verify_status_update(self, plugin_id, status_data):
        """
        Weryfikuje autoryzację aktualizacji statusu wtyczki.

        Args:
            plugin_id (str): Identyfikator wtyczki
            status_data (dict): Dane statusu zawierające token autoryzacji

        Returns:
            bool: True jeśli aktualizacja jest autoryzowana, False w przeciwnym wypadku
        """
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            return False

        auth_token = status_data.get("auth_token")
        if not auth_token or plugin.get("api_key") != auth_token:
            return False

        return True

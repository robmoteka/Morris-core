#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moduł Chain Engine dla systemu Morris.
Odpowiada za uruchamianie chainów (przepływów) w odpowiedzi na triggery.
"""

import json
import logging
import importlib
import threading
import time
import os
from queue import Queue

# Konfiguracja loggera
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChainEngine:
    """
    Silnik przetwarzania chainów (przepływów) w systemie Morris.
    Obsługuje uruchamianie chainów w odpowiedzi na triggery oraz przetwarzanie danych przez wtyczki.
    """

    def __init__(self, mqtt_client=None, chains_file="data/chains.json"):
        """
        Inicjalizacja silnika chainów.

        Args:
            mqtt_client: Instancja klienta MQTT do komunikacji z zdalnymi wtyczkami.
            chains_file (str): Ścieżka do pliku z definicjami chainów.
        """
        self.mqtt_client = mqtt_client
        self.chains_file = chains_file
        self.chains = {}
        self.plugins = {}
        self.remote_responses = {}
        self.response_queues = {}

        # Wczytanie chainów z pliku
        self.load_chains()

        # Konfiguracja callbacków MQTT dla zdalnych wtyczek
        if self.mqtt_client:
            self._setup_mqtt_callbacks()

    def load_chains(self):
        """
        Ładuje definicje chainów z pliku JSON.
        """
        if not os.path.exists(self.chains_file):
            logger.warning(
                f"Plik z definicjami chainów nie istnieje: {self.chains_file}"
            )
            return

        try:
            with open(self.chains_file, "r") as f:
                chains_data = json.load(f)

            # Weryfikacja i dodanie chainów
            for chain_id, chain_definition in chains_data.items():
                if self._validate_chain(chain_definition):
                    self.chains[chain_id] = chain_definition
                    logger.info(f"Załadowano chain: {chain_id}")
                else:
                    logger.error(f"Nieprawidłowa definicja chaina: {chain_id}")

            logger.info(
                f"Załadowano {len(self.chains)} chainów z pliku {self.chains_file}"
            )

        except Exception as e:
            logger.error(f"Błąd podczas ładowania chainów: {e}")

    def _validate_chain(self, chain_definition):
        """
        Sprawdza poprawność definicji chaina.

        Args:
            chain_definition (dict): Definicja chaina do sprawdzenia

        Returns:
            bool: True jeśli definicja jest poprawna, False w przeciwnym wypadku
        """
        # Sprawdzenie, czy definicja zawiera wymagane pola
        if not isinstance(chain_definition, dict):
            logger.error("Definicja chaina musi być słownikiem")
            return False

        if "trigger" not in chain_definition:
            logger.error("Definicja chaina musi zawierać pole 'trigger'")
            return False

        if "steps" not in chain_definition or not isinstance(
            chain_definition["steps"], list
        ):
            logger.error("Definicja chaina musi zawierać pole 'steps' będące listą")
            return False

        # Sprawdzenie, czy wszystkie kroki mają zdefiniowany plugin
        for i, step in enumerate(chain_definition["steps"]):
            if not isinstance(step, dict) or "plugin" not in step:
                logger.error(f"Krok {i} nie zawiera wymaganego pola 'plugin'")
                return False

        return True

    def get_chain_for_trigger(self, trigger_id):
        """
        Znajduje chain pasujący do podanego triggera.

        Args:
            trigger_id (str): Identyfikator triggera

        Returns:
            tuple: (chain_id, chain_definition) lub (None, None) jeśli nie znaleziono
        """
        for chain_id, chain in self.chains.items():
            if chain.get("trigger") == trigger_id:
                return chain_id, chain

        return None, None

    def add_chain(self, chain_id, chain_definition):
        """
        Dodaje nowy chain do systemu.

        Args:
            chain_id (str): Identyfikator chaina
            chain_definition (dict): Definicja chaina

        Returns:
            bool: True jeśli dodanie się powiodło, False w przeciwnym wypadku
        """
        if not self._validate_chain(chain_definition):
            logger.error(f"Nie można dodać chaina {chain_id} - nieprawidłowa definicja")
            return False

        self.chains[chain_id] = chain_definition
        logger.info(f"Dodano chain: {chain_id}")

        # Zapisanie zaktualizowanych chainów do pliku
        self._save_chains()

        return True

    def remove_chain(self, chain_id):
        """
        Usuwa chain z systemu.

        Args:
            chain_id (str): Identyfikator chaina do usunięcia

        Returns:
            bool: True jeśli usunięcie się powiodło, False w przeciwnym wypadku
        """
        if chain_id not in self.chains:
            logger.warning(f"Nie można usunąć chaina {chain_id} - nie istnieje")
            return False

        del self.chains[chain_id]
        logger.info(f"Usunięto chain: {chain_id}")

        # Zapisanie zaktualizowanych chainów do pliku
        self._save_chains()

        return True

    def _save_chains(self):
        """
        Zapisuje definicje chainów do pliku JSON.
        """
        try:
            # Upewnienie się, że katalog istnieje
            os.makedirs(os.path.dirname(self.chains_file), exist_ok=True)

            with open(self.chains_file, "w") as f:
                json.dump(self.chains, f, indent=4)

            logger.info(
                f"Zapisano {len(self.chains)} chainów do pliku {self.chains_file}"
            )

        except Exception as e:
            logger.error(f"Błąd podczas zapisywania chainów: {e}")

    def run_chain(self, trigger_id, payload):
        """
        Uruchamia chain pasujący do podanego triggera.

        Args:
            trigger_id (str): Identyfikator triggera
            payload (dict): Dane wejściowe do przetworzenia

        Returns:
            dict: Wynik przetwarzania przez chain
        """
        # Znalezienie chaina dla triggera
        chain_id, chain = self.get_chain_for_trigger(trigger_id)

        if not chain_id:
            logger.warning(f"Nie znaleziono chaina dla triggera: {trigger_id}")
            return payload

        logger.info(f"Uruchamianie chaina '{chain_id}' dla triggera '{trigger_id}'")

        # Kopia danych wejściowych, aby nie modyfikować oryginału
        current_data = payload.copy() if isinstance(payload, dict) else payload

        # Wykonanie każdego kroku w chainie
        for step_index, step in enumerate(chain.get("steps", [])):
            plugin_name = step.get("plugin", "")
            plugin_config = step.get("config", {})

            logger.info(f"Krok {step_index+1}: Uruchamianie pluginu '{plugin_name}'")

            try:
                # Sprawdzenie, czy to plugin lokalny czy zdalny
                if ":" in plugin_name:
                    # Plugin zdalny (np. "remote:device1:temperature")
                    current_data = self._run_remote_plugin(
                        plugin_name, current_data, plugin_config
                    )
                else:
                    # Plugin lokalny
                    current_data = self._run_local_plugin(
                        plugin_name, current_data, plugin_config
                    )

            except Exception as e:
                logger.error(
                    f"Błąd podczas wykonywania kroku {step_index+1} (plugin '{plugin_name}'): {e}"
                )
                # Kontynuujemy przetwarzanie mimo błędu, aby nie przerywać całego chaina

        logger.info(f"Zakończono przetwarzanie chaina '{chain_id}'")
        return current_data

    def run_chain_async(self, trigger_id, payload, callback=None):
        """
        Asynchronicznie uruchamia chain pasujący do podanego triggera.

        Args:
            trigger_id (str): Identyfikator triggera
            payload (dict): Dane wejściowe do przetworzenia
            callback (function, optional): Funkcja wywoływana po zakończeniu przetwarzania
        """

        def _run_chain_thread():
            result = self.run_chain(trigger_id, payload)
            if callback:
                callback(result)

        # Uruchomienie przetwarzania w osobnym wątku
        thread = threading.Thread(target=_run_chain_thread)
        thread.daemon = True
        thread.start()

        logger.info(
            f"Uruchomiono asynchroniczne przetwarzanie chaina dla triggera '{trigger_id}'"
        )

    def _run_local_plugin(self, plugin_name, data, config):
        """
        Uruchamia lokalny plugin.

        Args:
            plugin_name (str): Nazwa pluginu
            data (dict): Dane wejściowe
            config (dict): Konfiguracja pluginu

        Returns:
            dict: Wynik przetwarzania przez plugin
        """
        try:
            # Konwersja nazwy pluginu z PascalCase na snake_case dla importu
            module_name = "".join(
                ["_" + c.lower() if c.isupper() else c for c in plugin_name]
            ).lstrip("_")
            module_path = f"plugins.{module_name}"

            logger.info(f"Próba importu modułu: {module_path}")
            module = importlib.import_module(module_path)

            # Utworzenie instancji pluginu
            plugin_class = getattr(module, plugin_name)
            logger.info(f"Tworzenie instancji pluginu: {plugin_name}")
            plugin = plugin_class(config)

            # Uruchomienie pluginu
            logger.info(f"Uruchamianie pluginu: {plugin_name}")
            result = plugin.process(data)

            return result

        except ImportError as e:
            logger.error(f"Nie można zaimportować pluginu: {plugin_name}. Błąd: {e}")
            return data

        except AttributeError as e:
            logger.error(f"Nie znaleziono klasy pluginu '{plugin_name}': {e}")
            return data

        except Exception as e:
            logger.error(f"Błąd podczas uruchamiania pluginu '{plugin_name}': {e}")
            return data

    def _run_remote_plugin(self, plugin_name, data, config):
        """
        Uruchamia zdalny plugin poprzez MQTT.

        Args:
            plugin_name (str): Nazwa pluginu w formacie "remote:device:plugin"
            data (dict): Dane wejściowe
            config (dict): Konfiguracja pluginu

        Returns:
            dict: Wynik przetwarzania przez plugin
        """
        if not self.mqtt_client:
            logger.error("Nie można uruchomić zdalnego pluginu - brak klienta MQTT")
            return data

        try:
            # Parsowanie nazwy pluginu
            parts = plugin_name.split(":")
            if len(parts) < 3:
                logger.error(f"Nieprawidłowa nazwa zdalnego pluginu: {plugin_name}")
                return data

            device_id = parts[1]
            plugin_id = parts[2]

            # Przygotowanie danych do wysłania
            request_data = {
                "action": "run_plugin",
                "plugin_id": plugin_id,
                "data": data,
                "config": config,
            }

            # Publikacja żądania
            topic = f"plugin/{device_id}/input"
            self.mqtt_client.publish(topic=topic, payload=request_data)

            logger.info(f"Wysłano żądanie do zdalnego pluginu '{plugin_name}'")

            # UWAGA: W obecnej implementacji nie czekamy na odpowiedź od zdalnego pluginu
            # W przyszłości można dodać mechanizm oczekiwania na odpowiedź

            return data

        except Exception as e:
            logger.error(
                f"Błąd podczas uruchamiania zdalnego pluginu '{plugin_name}': {e}"
            )
            return data

    def _handle_plugin_response(self, msg):
        """
        Obsługuje odpowiedź od zdalnej wtyczki.

        Args:
            msg: Wiadomość MQTT zawierająca odpowiedź od zdalnej wtyczki
        """
        try:
            # Parsowanie tematu wiadomości
            topic_parts = msg.topic.split("/")
            if len(topic_parts) < 3:
                logger.error(f"Nieprawidłowy format tematu odpowiedzi: {msg.topic}")
                return

            device_id = topic_parts[1]
            response_key = f"plugin/{device_id}"

            # Parsowanie treści wiadomości
            try:
                payload = json.loads(msg.payload.decode())
            except json.JSONDecodeError:
                logger.error(
                    f"Otrzymana odpowiedź nie jest poprawnym JSON: {msg.payload}"
                )
                return

            logger.debug(
                f"Otrzymano odpowiedź od zdalnej wtyczki {device_id}: {payload}"
            )

            # Jeśli istnieje kolejka dla tej wtyczki, dodaj odpowiedź
            if response_key in self.response_queues:
                self.response_queues[response_key].put(payload)

            # Zapisz odpowiedź w słowniku (dla kompatybilności)
            self.remote_responses[response_key] = payload

        except Exception as e:
            logger.error(
                f"Błąd podczas przetwarzania odpowiedzi od zdalnej wtyczki: {e}"
            )

    def _setup_mqtt_callbacks(self):
        """
        Konfiguruje callbacki MQTT dla obsługi odpowiedzi od zdalnych wtyczek.
        """
        if not self.mqtt_client:
            logger.warning("Brak klienta MQTT - nie można skonfigurować callbacków")
            return

        # Sprawdzenie, czy klient MQTT jest już zainicjalizowany
        if not hasattr(self.mqtt_client, "client") or self.mqtt_client.client is None:
            logger.warning(
                "Klient MQTT nie jest jeszcze zainicjalizowany - callbacki zostaną skonfigurowane później"
            )
            return

        # Zapisanie oryginalnego callbacka
        original_on_message = self.mqtt_client.client.on_message

        # Utworzenie wrappera dla callbacka on_message
        def on_message_wrapper(client, userdata, msg):
            # Sprawdzenie, czy wiadomość jest odpowiedzią od zdalnej wtyczki
            if msg.topic.startswith("plugin/") and msg.topic.endswith("/output"):
                self._handle_plugin_response(msg)

            # Wywołanie oryginalnego callbacka
            if original_on_message:
                original_on_message(client, userdata, msg)

        # Ustawienie wrappera jako callbacka
        self.mqtt_client.client.on_message = on_message_wrapper

        logger.info("Skonfigurowano callbacki MQTT dla zdalnych wtyczek")

    def _process_remote_plugin(self, plugin_name, data, params=None, timeout=5):
        """
        Przetwarza dane przez zdalną wtyczkę za pomocą MQTT.

        Args:
            plugin_name (str): Nazwa zdalnej wtyczki (bez prefiksu 'remote:').
            data (dict): Dane do przetworzenia.
            params (dict, optional): Parametry dla wtyczki. Domyślnie None.
            timeout (int, optional): Maksymalny czas oczekiwania na odpowiedź w sekundach. Domyślnie 5.

        Returns:
            dict: Przetworzone dane lub oryginalne dane w przypadku błędu.
        """
        if not self.mqtt_client:
            logger.error(
                f"Brak klienta MQTT. Nie można wywołać zdalnej wtyczki {plugin_name}."
            )
            return data

        # Przygotowanie danych do wysłania
        request_data = {"data": data, "params": params or {}}

        # Klucz dla odpowiedzi
        response_key = f"plugin/{plugin_name}"

        # Utworzenie kolejki dla odpowiedzi
        response_queue = Queue()
        self.response_queues[response_key] = response_queue

        # Wyczyszczenie poprzedniej odpowiedzi
        if response_key in self.remote_responses:
            del self.remote_responses[response_key]

        # Wysłanie danych do zdalnej wtyczki
        input_topic = f"plugin/{plugin_name}/input"
        self.mqtt_client.publish(topic=input_topic, payload=request_data)
        logger.info(f"Wysłano dane do zdalnej wtyczki {plugin_name}")

        try:
            # Oczekiwanie na odpowiedź
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    # Próba pobrania odpowiedzi z kolejki
                    response = response_queue.get(block=False)

                    # Usunięcie kolejki
                    del self.response_queues[response_key]

                    # Zwrócenie przetworzonych danych
                    return response.get("data", data)
                except Exception:
                    # Brak odpowiedzi, czekaj dalej
                    time.sleep(0.1)

            # Timeout - brak odpowiedzi w określonym czasie
            logger.warning(
                f"Timeout podczas oczekiwania na odpowiedź od zdalnej wtyczki {plugin_name}"
            )

            # Usunięcie kolejki
            del self.response_queues[response_key]

            return data

        except Exception as e:
            logger.error(
                f"Błąd podczas przetwarzania przez zdalną wtyczkę {plugin_name}: {e}"
            )

            # Usunięcie kolejki w przypadku błędu
            if response_key in self.response_queues:
                del self.response_queues[response_key]

            return data

    def _get_plugin_instance(self, plugin_name):
        """
        Pobiera lub tworzy instancję wtyczki.

        Args:
            plugin_name (str): Nazwa wtyczki.

        Returns:
            BasePlugin: Instancja wtyczki lub None w przypadku błędu.
        """
        # Sprawdzenie, czy wtyczka jest już załadowana
        if plugin_name in self.plugins:
            return self.plugins[plugin_name]

        try:
            # Dynamiczne importowanie modułu wtyczki
            module_name = f"plugins.{plugin_name.lower()}"
            module = importlib.import_module(module_name)

            # Pobranie klasy wtyczki
            plugin_class = getattr(module, plugin_name)

            # Utworzenie instancji wtyczki
            plugin_instance = plugin_class()

            # Zapisanie instancji do cache'a
            self.plugins[plugin_name] = plugin_instance

            return plugin_instance
        except Exception as e:
            logger.error(f"Błąd podczas ładowania wtyczki {plugin_name}: {e}")
            return None

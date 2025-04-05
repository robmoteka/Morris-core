#!/usr/bin/env python3
"""
Skrypt do zarządzania aplikacją Morris.
Umożliwia uruchamianie, zatrzymywanie i sprawdzanie statusu aplikacji i jej procesów.
"""

import os
import sys
import signal
import subprocess
import time
import json
import psutil
import logging
from pathlib import Path


# Funkcja sprawdzająca, czy skrypt działa w środowisku wirtualnym
def czy_venv_aktywne():
    """
    Sprawdza, czy skrypt jest uruchamiany w środowisku wirtualnym.
    Zwraca True, jeśli venv jest aktywne, False w przeciwnym przypadku.
    """
    return (
        hasattr(sys, "prefix")
        and hasattr(sys, "base_prefix")
        and sys.prefix != sys.base_prefix
    )


# Konfiguracja loggera
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("morris.log")],
)
logger = logging.getLogger("morris-manager")

# Stałe
PID_FILE = "morris.pid"
MQTT_PID_FILE = "mqtt.pid"
APP_PORT = 30331


def zapisz_pid(plik, pid):
    """
    Zapisuje PID procesu do pliku.

    Args:
        plik (str): Nazwa pliku do zapisu PID
        pid (int): PID procesu
    """
    try:
        with open(plik, "w") as f:
            f.write(str(pid))
        logger.info(f"Zapisano PID {pid} do pliku {plik}")
    except Exception as e:
        logger.error(f"Błąd podczas zapisywania PID do pliku: {e}")


def odczytaj_pid(plik):
    """
    Odczytuje PID z pliku.

    Args:
        plik (str): Nazwa pliku z PID

    Returns:
        int: PID procesu lub None jeśli nie znaleziono
    """
    try:
        if os.path.exists(plik):
            with open(plik, "r") as f:
                return int(f.read().strip())
        return None
    except Exception as e:
        logger.error(f"Błąd podczas odczytywania PID z pliku: {e}")
        return None


def czy_proces_dziala(pid):
    """
    Sprawdza czy proces o podanym PID działa.

    Args:
        pid (int): PID procesu

    Returns:
        bool: True jeśli proces działa, False w przeciwnym przypadku
    """
    if pid is None:
        return False

    try:
        proces = psutil.Process(pid)
        return proces.is_running()
    except psutil.NoSuchProcess:
        return False
    except Exception as e:
        logger.error(f"Błąd podczas sprawdzania procesu: {e}")
        return False


def czy_port_zajety(port):
    """
    Sprawdza czy port jest zajęty.

    Args:
        port (int): Numer portu

    Returns:
        bool: True jeśli port jest zajęty, False w przeciwnym przypadku
    """
    for conn in psutil.net_connections("inet"):
        if conn.laddr.port == port and conn.status == "LISTEN":
            return True
    return False


def znajdz_potomne_procesy(pid):
    """
    Znajduje wszystkie procesy potomne dla danego PID.

    Args:
        pid (int): PID procesu rodzica

    Returns:
        list: Lista PID procesów potomnych
    """
    try:
        rodzic = psutil.Process(pid)
        potomne = rodzic.children(recursive=True)
        return [p.pid for p in potomne]
    except psutil.NoSuchProcess:
        return []
    except Exception as e:
        logger.error(f"Błąd podczas znajdowania procesów potomnych: {e}")
        return []


def start():
    """
    Uruchamia aplikację Morris.
    """
    # Sprawdzenie czy aplikacja już nie działa
    appPid = odczytaj_pid(PID_FILE)
    if czy_proces_dziala(appPid):
        logger.warning(f"Aplikacja Morris już działa (PID: {appPid})")
        return False

    if czy_port_zajety(APP_PORT):
        logger.warning(f"Port {APP_PORT} jest już zajęty przez inny proces")
        return False

    try:
        # Uruchomienie aplikacji w tle z przekierowaniem wyjścia do plików logów
        logger.info("Uruchamianie aplikacji Morris...")
        proces = subprocess.Popen(
            [sys.executable, "app.py"],
            stdout=open("app_out.log", "w"),
            stderr=open("app_err.log", "w"),
            preexec_fn=os.setsid,
        )

        # Zapisanie PID głównego procesu
        zapisz_pid(PID_FILE, proces.pid)

        # Odczekanie chwili na uruchomienie aplikacji
        time.sleep(2)

        # Sprawdzenie czy proces nadal działa (czy nie zakończył się błędem)
        if not czy_proces_dziala(proces.pid):
            logger.error(
                "Aplikacja zakończyła działanie tuż po uruchomieniu. Sprawdź logi."
            )
            return False

        # Znalezienie i zapisanie procesu MQTT
        potomne = znajdz_potomne_procesy(proces.pid)
        if potomne:
            zapisz_pid(MQTT_PID_FILE, potomne[0])
            logger.info(f"Zapisano PID procesu MQTT: {potomne[0]}")

        # Sprawdzenie czy serwer webowy działa i odpowiada na żądania
        try:
            import requests
            from requests.exceptions import RequestException

            # Dajemy aplikacji trochę więcej czasu na pełne uruchomienie
            time.sleep(3)

            try:
                response = requests.get(f"http://localhost:{APP_PORT}/")
                if response.status_code == 200:
                    logger.info(
                        f"Aplikacja webowa działa poprawnie na porcie {APP_PORT}"
                    )
                else:
                    logger.warning(
                        f"Aplikacja webowa zwraca kod: {response.status_code}"
                    )
            except RequestException as e:
                logger.error(f"Nie można połączyć się z aplikacją webową: {e}")
                logger.error(
                    "Proces został uruchomiony, ale serwer webowy nie odpowiada."
                )
                logger.error("Sprawdź logi w plikach app_out.log i app_err.log")
        except ImportError:
            logger.warning(
                "Moduł requests nie jest zainstalowany. Nie można sprawdzić dostępności serwera webowego."
            )

        logger.info(f"Aplikacja Morris została uruchomiona (PID: {proces.pid})")
        return True

    except Exception as e:
        logger.error(f"Błąd podczas uruchamiania aplikacji: {e}")
        return False


def stop():
    """
    Zatrzymuje aplikację Morris i proces MQTT.

    Returns:
        bool: True jeśli zatrzymanie powiodło się, False w przeciwnym przypadku
    """
    success = True

    # Zatrzymanie głównego procesu aplikacji
    appPid = odczytaj_pid(PID_FILE)
    if czy_proces_dziala(appPid):
        try:
            # Znajdź wszystkie procesy potomne
            potomne = znajdz_potomne_procesy(appPid)

            # Zatrzymaj główny proces (wysyłając SIGTERM do całej grupy procesów)
            os.killpg(os.getpgid(appPid), signal.SIGTERM)
            logger.info(f"Wysłano sygnał SIGTERM do procesu głównego (PID: {appPid})")

            # Odczekaj chwilę
            time.sleep(2)

            # Sprawdź czy procesy nadal działają i zakończ je siłowo jeśli trzeba
            if czy_proces_dziala(appPid):
                os.killpg(os.getpgid(appPid), signal.SIGKILL)
                logger.warning(
                    f"Proces główny nadal działał, wysłano SIGKILL (PID: {appPid})"
                )

            # Usuń plik PID
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)

            logger.info("Aplikacja Morris została zatrzymana")

        except Exception as e:
            logger.error(f"Błąd podczas zatrzymywania aplikacji: {e}")
            success = False
    else:
        logger.info("Aplikacja Morris nie jest uruchomiona")

    # Upewnij się, że proces MQTT również został zatrzymany
    mqttPid = odczytaj_pid(MQTT_PID_FILE)
    if czy_proces_dziala(mqttPid):
        try:
            os.kill(mqttPid, signal.SIGTERM)
            logger.info(f"Wysłano sygnał SIGTERM do procesu MQTT (PID: {mqttPid})")

            # Odczekaj chwilę
            time.sleep(1)

            # Sprawdź czy proces nadal działa i zakończ go siłowo jeśli trzeba
            if czy_proces_dziala(mqttPid):
                os.kill(mqttPid, signal.SIGKILL)
                logger.warning(
                    f"Proces MQTT nadal działał, wysłano SIGKILL (PID: {mqttPid})"
                )

            # Usuń plik PID
            if os.path.exists(MQTT_PID_FILE):
                os.remove(MQTT_PID_FILE)

        except Exception as e:
            logger.error(f"Błąd podczas zatrzymywania procesu MQTT: {e}")
            success = False

    return success


def restart():
    """
    Restartuje aplikację Morris.

    Returns:
        bool: True jeśli restart powiódł się, False w przeciwnym przypadku
    """
    logger.info("Restartuję aplikację Morris...")

    # Zatrzymanie aplikacji
    stop()

    # Odczekanie chwili
    time.sleep(2)

    # Uruchomienie aplikacji
    return start()


def status():
    """
    Sprawdza status aplikacji Morris i procesu MQTT.

    Returns:
        dict: Słownik ze statusem aplikacji i procesu MQTT
    """
    statusInfo = {
        "aplikacja": {"dziala": False, "pid": None},
        "mqtt": {"dziala": False, "pid": None},
        "port": {"zajety": czy_port_zajety(APP_PORT), "numer": APP_PORT},
    }

    # Sprawdzenie statusu głównej aplikacji
    appPid = odczytaj_pid(PID_FILE)
    if czy_proces_dziala(appPid):
        statusInfo["aplikacja"]["dziala"] = True
        statusInfo["aplikacja"]["pid"] = appPid

    # Sprawdzenie statusu procesu MQTT
    mqttPid = odczytaj_pid(MQTT_PID_FILE)
    if czy_proces_dziala(mqttPid):
        statusInfo["mqtt"]["dziala"] = True
        statusInfo["mqtt"]["pid"] = mqttPid

    return statusInfo


def wyswietl_status():
    """
    Wyświetla status aplikacji Morris i procesu MQTT.
    """
    statusInfo = status()

    print("\n=== Status aplikacji Morris ===")
    print(
        f"Główny proces: {'DZIAŁA' if statusInfo['aplikacja']['dziala'] else 'NIE DZIAŁA'}"
    )
    if statusInfo["aplikacja"]["pid"]:
        print(f"PID głównego procesu: {statusInfo['aplikacja']['pid']}")

    print(
        f"\nProces MQTT: {'DZIAŁA' if statusInfo['mqtt']['dziala'] else 'NIE DZIAŁA'}"
    )
    if statusInfo["mqtt"]["pid"]:
        print(f"PID procesu MQTT: {statusInfo['mqtt']['pid']}")

    print(
        f"\nPort {statusInfo['port']['numer']}: {'ZAJĘTY' if statusInfo['port']['zajety'] else 'WOLNY'}"
    )
    print("================================\n")


def main():
    """
    Główna funkcja programu.
    """
    if len(sys.argv) < 2:
        print(
            """
Użycie: python morris.py [opcja]

Opcje:
  start   - Uruchamia aplikację Morris
  stop    - Zatrzymuje aplikację Morris
  restart - Restartuje aplikację Morris
  status  - Wyświetla status aplikacji Morris
        """
        )
        sys.exit(1)

    komenda = sys.argv[1].lower()

    if komenda == "start":
        if start():
            print("Aplikacja Morris została uruchomiona")
            sys.exit(0)
        else:
            print("Nie udało się uruchomić aplikacji Morris")
            sys.exit(1)

    elif komenda == "stop":
        if stop():
            print("Aplikacja Morris została zatrzymana")
            sys.exit(0)
        else:
            print("Wystąpiły problemy podczas zatrzymywania aplikacji Morris")
            sys.exit(1)

    elif komenda == "restart":
        if restart():
            print("Aplikacja Morris została zrestartowana")
            sys.exit(0)
        else:
            print("Nie udało się zrestartować aplikacji Morris")
            sys.exit(1)

    elif komenda == "status":
        wyswietl_status()
        sys.exit(0)

    else:
        print(f"Nieznana opcja: {komenda}")
        sys.exit(1)


if __name__ == "__main__":
    main()

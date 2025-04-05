#!/bin/bash

# venv.sh - Skrypt do zarządzania środowiskiem wirtualnym Pythona dla projektu Morris-core
# Autor: Cascade AI Assistant
# Data: 2025-04-05

# Kolory do komunikatów
CZERWONY='\033[0;31m'
ZIELONY='\033[0;32m'
ZOLTY='\033[1;33m'
NIEBIESKI='\033[0;34m'
RESET='\033[0m'

# Ścieżka do środowiska wirtualnego
VENV_PATH=".venv"

# Funkcja do wyświetlania komunikatów
wyswietl_komunikat() {
    local typ=$1
    local komunikat=$2
    
    case "$typ" in
        "info")
            echo -e "${NIEBIESKI}[INFO]${RESET} $komunikat"
            ;;
        "sukces")
            echo -e "${ZIELONY}[SUKCES]${RESET} $komunikat"
            ;;
        "ostrzezenie")
            echo -e "${ZOLTY}[OSTRZEŻENIE]${RESET} $komunikat"
            ;;
        "blad")
            echo -e "${CZERWONY}[BŁĄD]${RESET} $komunikat"
            ;;
        *)
            echo "$komunikat"
            ;;
    esac
}

# Sprawdzenie czy Python jest zainstalowany
if ! command -v python3 &> /dev/null; then
    wyswietl_komunikat "blad" "Python 3 nie jest zainstalowany. Zainstaluj Python 3 i spróbuj ponownie."
    exit 1
fi

# Sprawdzenie czy środowisko wirtualne istnieje
if [ ! -d "$VENV_PATH" ]; then
    wyswietl_komunikat "info" "Tworzenie środowiska wirtualnego w $VENV_PATH..."
    python3 -m venv $VENV_PATH
    
    if [ $? -ne 0 ]; then
        wyswietl_komunikat "blad" "Nie udało się utworzyć środowiska wirtualnego. Upewnij się, że pakiet 'python3-venv' jest zainstalowany."
        exit 1
    fi
    
    wyswietl_komunikat "sukces" "Środowisko wirtualne zostało utworzone."
else
    wyswietl_komunikat "info" "Środowisko wirtualne już istnieje."
fi

# Aktywacja środowiska wirtualnego
wyswietl_komunikat "info" "Aktywacja środowiska wirtualnego..."
source "$VENV_PATH/bin/activate"

if [ $? -ne 0 ]; then
    wyswietl_komunikat "blad" "Nie udało się aktywować środowiska wirtualnego."
    exit 1
fi

# Sprawdzenie wersji Python w środowisku wirtualnym
PYTHON_VERSION=$(python --version)
wyswietl_komunikat "info" "Używany Python: $PYTHON_VERSION"

# Aktualizacja pip do najnowszej wersji
wyswietl_komunikat "info" "Aktualizacja pip do najnowszej wersji..."
pip install --upgrade pip > /dev/null

# Sprawdzenie czy plik requirements.txt istnieje
if [ -f "requirements.txt" ]; then
    wyswietl_komunikat "info" "Znaleziono plik requirements.txt. Instalacja wymaganych pakietów..."
    pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        wyswietl_komunikat "blad" "Wystąpił błąd podczas instalacji pakietów z requirements.txt."
        wyswietl_komunikat "info" "Możesz spróbować zainstalować je ręcznie używając: pip install -r requirements.txt"
    else
        wyswietl_komunikat "sukces" "Wszystkie wymagane pakiety zostały zainstalowane."
    fi
else
    wyswietl_komunikat "ostrzezenie" "Nie znaleziono pliku requirements.txt."
    wyswietl_komunikat "info" "Instalacja podstawowych pakietów dla projektu Morris-core..."
    
    # Instalacja podstawowych pakietów dla projektu Morris-core
    pip install flask flask-login psutil paho-mqtt > /dev/null
    
    if [ $? -ne 0 ]; then
        wyswietl_komunikat "blad" "Wystąpił błąd podczas instalacji podstawowych pakietów."
    else
        wyswietl_komunikat "sukces" "Podstawowe pakiety zostały zainstalowane."
        wyswietl_komunikat "info" "Tworzenie pliku requirements.txt..."
        pip freeze > requirements.txt
        wyswietl_komunikat "sukces" "Plik requirements.txt został utworzony."
    fi
fi

# Wyświetlenie informacji o aktywnym środowisku
wyswietl_komunikat "sukces" "Środowisko wirtualne zostało aktywowane."
wyswietl_komunikat "info" "Aby dezaktywować środowisko, wpisz: deactivate"
wyswietl_komunikat "info" "Możesz teraz uruchomić aplikację: ./morris.py start"

# Wyświetlenie zainstalowanych pakietów
wyswietl_komunikat "info" "Zainstalowane pakiety:"
pip list

# Pozostawienie aktywnego środowiska
exec "${SHELL}"
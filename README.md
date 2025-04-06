# Projekt Morris

## Opis

Morris to modularna aplikacja zarządzająca przepływem danych z pomocą chainów i wtyczek (plugins), z rozproszoną architekturą i komunikacją przez MQTT + WebHook + REST.

## Architektura

- **Backend**: Python + Flask
- **Komunikacja**: MQTT (jako message bus), REST API, webhooki
- **Rozproszenie**: konektory działają na VPS-ach lub w sieci lokalnej

## Struktura projektu

```
morris/
├── app.py             # punkt startowy aplikacji
├── mqtt_client.py     # osobny wątek do MQTT
├── routes/
│   └── webhook.py     # obsługa webhooków
├── core/
│   └── chain_engine.py # silnik przetwarzania chainów
├── plugins/
│   ├── base.py        # bazowa klasa dla wszystkich wtyczek
│   ├── log_plugin.py  # wtyczka do logowania danych
│   └── uppercase_plugin.py # wtyczka do konwersji tekstu na wielkie litery
├── chains/
│   └── chains.json    # konfiguracja chainów
├── config/
│   └── mqtt.json      # konfiguracja połączenia z brokerem
├── templates/         # (na przyszłość: Jinja2)
├── static/            # (na przyszłość: Bootstrap/JS)
└── tests/             # testy jednostkowe
    ├── test_app.py
    ├── test_mqtt_client.py
    ├── test_webhook.py
    └── run_tests.py   # skrypt do uruchamiania wszystkich testów
```

## Funkcjonalności

- Aplikacja Flask z podstawową strukturą katalogów
- Obsługa webhooków pod adresem `/hook/<modul>` – metoda POST
- Przechwycenie danych JSON
- Klient MQTT do komunikacji z innymi komponentami
- Chain Engine do przetwarzania danych przez zdefiniowane chainy
- System wtyczek (plugins) do rozszerzania funkcjonalności
- REST API do zarządzania chainami
- Monitorowanie statusu wtyczek (online/offline/error/working)

## Endpointy

- `/` - strona główna z informacjami o aplikacji
- `/hook/<modul>` - endpoint do odbierania webhooków
- `/send-test` - endpoint do wysyłania testowej wiadomości MQTT
- `/chains` - zarządzanie chainami (GET, POST)
- `/chains/<chain_id>` - zarządzanie pojedynczym chainem (GET, PUT, DELETE)
- `/run-chain/<chain_id>` - ręczne uruchomienie chaina (POST)
- `/api/plugin-status/<plugin_id>` - aktualizacja statusu wtyczki (POST)

## Chain Engine

Chain Engine to główny komponent odpowiedzialny za przetwarzanie danych przez zdefiniowane chainy. Każdy chain składa się z:

- Triggera - identyfikatora, który uruchamia chain (np. `webhook:test` lub `mqtt:core/test`)
- Kroków - sekwencji wtyczek, które przetwarzają dane

Chainy są definiowane w pliku `chains/chains.json` w formacie:

```json
{
  "chain_id": {
    "trigger": "trigger_id",
    "steps": [
      {
        "plugin": "PluginName",
        "config": {
          "param1": "value1"
        }
      }
    ]
  }
}
```

## Wtyczki (Plugins)

Wtyczki to komponenty rozszerzające funkcjonalność aplikacji. Każda wtyczka dziedziczy po klasie `BasePlugin` i implementuje metodę `process(data, config)`, która przetwarza dane wejściowe i zwraca wynik.

Dostępne wtyczki:

- `LogPlugin` - loguje otrzymane dane i przekazuje je dalej bez zmian
- `UppercasePlugin` - konwertuje wartości tekstowe w danych wejściowych na wielkie litery

Statusy wtyczek:

- `online` - wtyczka działa poprawnie
- `offline` - wtyczka jest wyłączona lub niedostępna
- `error` - wtyczka napotkała błąd
- `working` - wtyczka jest w trakcie przetwarzania

## Logo

Domyślnie, system szuka pliku logo w lokalizacji `static/images/morris_logo.png`.
Jeśli chcesz użyć własnego logo, zastąp ten plik swoim obrazem, zachowując tę samą nazwę pliku.

## Uruchomienie

```bash
python app.py
```

Aplikacja domyślnie działa na porcie 30331.

## Zarządzanie aplikacją

Do zarządzania aplikacją Morris i jej procesem MQTT służy skrypt `morris.py`. Jest to rekomendowany sposób uruchamiania i zatrzymywania aplikacji, który zapewnia prawidłowe zarządzanie procesami głównymi i potomnymi.

```bash
# Uruchomienie aplikacji
python morris.py start
# lub
./morris.py start

# Zatrzymanie aplikacji i wszystkich procesów potomnych
python morris.py stop
# lub
./morris.py stop

# Sprawdzenie statusu aplikacji
python morris.py status
# lub
./morris.py status

# Restart aplikacji
python morris.py restart
# lub
./morris.py restart
```

Skrypt automatycznie zarządza zarówno głównym procesem aplikacji, jak i procesem potomnym MQTT. Nie zaleca się używania innych metod do kontrolowania tych procesów (np. bezpośrednio kill, pkill, itp.), ponieważ może to prowadzić do pozostawiania "osieroconych" procesów.

## Testowanie

Przykładowe żądanie do webhooka:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"message": "test", "value": 42}' http://localhost:30331/hook/test
```

Ręczne uruchomienie chaina:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"message": "test", "value": 42}' http://localhost:30331/run-chain/test_chain
```

## Wymagane biblioteki

- flask
- paho-mqtt
- threading (dla MQTT clienta jako osobnego wątku)
- pytest (dla testów)
- pytest-cov (dla raportów pokrycia kodu)

## Uruchamianie testów

```bash
# Uruchomienie wszystkich testów
python tests/run_tests.py

# Alternatywnie, używając pytest
pytest

# Uruchomienie testów z raportem pokrycia kodu
pytest --cov=.
```

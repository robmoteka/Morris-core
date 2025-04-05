Etap 2: Webowy Panel Administracyjny
📌 Opis projektu: Morris
Modularna, rozproszona aplikacja sterująca przepływem danych z pomocą tzw. „chainów”, uruchamianych przez webhooki, MQTT i REST API. Aplikacja umożliwia obsługę lokalnych i zdalnych wtyczek. Panel administracyjny służy do zarządzania chainami i pluginami.

Pełen opis projektu znajduje się w pliku Opis Modulu Core.md.

🎯 Aktualne zadanie:
Zaimplementuj webowy interfejs użytkownika (oparty o Flask + Jinja2 + Bootstrap), który umożliwia:

1. Zarządzanie chainami
   Wyświetlanie listy chainów z nazwą, triggerem i ilością kroków

Formularz edycji chaina:

Nazwa

Trigger (webhook, MQTT)

Kroki (plugin + konfiguracja jako JSON)

Możliwość dodawania i usuwania kroków dynamicznie (JS)

Zapis łańcucha jako JSON (np. chains.json lub przez API)

2. Zarządzanie pluginami
   Widok listy z kolumnami: nazwa, typ (local, mqtt, rest), status, opis

Przycisk dodania pluginu ręcznie (formularz POST)

Integracja z Plugin Managerem (czytanie z plugins.json lub API)

3. UI
   Bootstrap 5 do stylizacji (prosty i funkcjonalny layout)

Możliwość dynamicznej edycji kroków chaina przez JavaScript

Szablony Jinja2:

chains/list.html

chains/edit.html

plugins/list.html

📁 Struktura plików sugerowana
bash
Copy
Edit
morris/
├── templates/
│ └── chains/list.html
│ └── chains/edit.html
│ └── plugins/list.html
├── static/
│ └── js/form_chains.js
├── routes/
│ └── chains.py
│ └── plugins.py
📚 WAŻNE: Dodatkowe wytyczne
Proszę sprawdzać pliki Markdown (\*.md) znajdujące się w głównym katalogu projektu – zawierają:

opis architektury (np. Opis Modulu Core.md)

opis działania chainów

typy wtyczek i sposób ich obsługi

zasady integracji z backendem

🧪 Sprawdzenie poprawności
Zwróć uwagę, czy:

Chain można utworzyć, edytować i zapisać

Lista pluginów pokazuje aktualne dane

Wszystkie ścieżki są powiązane z backendem (np. GET /chains, POST /chains/save, GET /plugins)

Dane są walidowane po stronie serwera i/lub przeglądarki

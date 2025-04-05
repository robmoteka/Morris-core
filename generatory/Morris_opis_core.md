# Asystent Morris – Opis Modułu Core

---

## 1. Główne założenia

- Backend: **Python + Flask**
- Frontend: **Panel webowy** (Jinja2 + Bootstrap + JS)
- Komunikacja: **MQTT (message bus)**, **REST API**, **WebHooki**
- Architektura: **rozproszona** – konektory działające na VPS lub w sieci lokalnej

---

## 2. Morris (moduł główny)

- Aplikacja Flask jako centrum sterujące
- MQTT client (sub/publish)
- Obsługa webhooków: `/hook/<modul>`
- REST API: sterowanie, status, edycja chainów i wtyczek
- Webowy panel administracyjny:
  - Lista chainów
  - Edytor chaina (formularze)
  - Zarządzanie wtyczkami

---

## 3. Wtyczki (Plugins)

- Interfejs: `input -> process -> output`
- Typy: lokalne / mikroserwisy (MQTT lub REST)
- Automatyczna rejestracja przez `plugin/announce`
- Konfiguracja: dynamiczna (formularze/JSON)

---

## 4. Chainy (Przepływy)

- Definiowane przez użytkownika (JSON, YAML, UI)
- Triggerowane przez:

  - Webhooki (np. WhatsApp)
  - MQTT (np. dane z Smart Home)
  - Zegar/cykl czasu (np. co 10 minut)
  - **Actions** – zaplanowane wyzwalacze z parametrami wejściowymi

- Chainy mogą:
  - Rozpoczynać się od pluginów przetwarzających lub publikujących dane (MQTT/REST)
  - Mieć logikę warunkową (w przyszłości)
  - Składać się z kroków uruchamiających pluginy z przekazaniem parametrów

### Przykład chaina:

```yaml
chain_name: whatsapp_to_notion
trigger: webhook:whatsapp/message
steps:
  - plugin: extract_message
  - plugin: detect_language
  - plugin: push_to_notion
```

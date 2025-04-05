# Webhooks w systemie Morris

Ten dokument zawiera wytyczne dla modeli językowych (LLM) dotyczące tworzenia i korzystania z webhooków w systemie Morris. Znajdziesz tu instrukcje, przykłady i najlepsze praktyki, które pomogą w efektywnym wykorzystaniu mechanizmu webhooków do integracji z systemem.

## Spis treści

1. [Architektura webhooków](#architektura-webhooków)
2. [Typy webhooków](#typy-webhooków)
3. [Struktura żądań i odpowiedzi](#struktura-żądań-i-odpowiedzi)
4. [Rejestracja endpointów](#rejestracja-endpointów)
5. [Obsługa webhooków](#obsługa-webhooków)
6. [Bezpieczeństwo](#bezpieczeństwo)
7. [Integracja z Chain Engine](#integracja-z-chain-engine)
8. [Najlepsze praktyki](#najlepsze-praktyki)
9. [Przykłady](#przykłady)

## Architektura webhooków

System Morris wykorzystuje webhooks do komunikacji z systemami zewnętrznymi i uruchamiania zdefiniowanych łańcuchów przetwarzania (chains) w odpowiedzi na zdarzenia HTTP. Webhook Engine odpowiada za:

- Rejestrację endpointów webhookowych
- Routing przychodzących żądań do odpowiednich łańcuchów przetwarzania
- Walidację danych wejściowych
- Dostarczanie odpowiedzi zwrotnych

Każdy webhook jest powiązany z określonym łańcuchem przetwarzania (chain), który zostanie uruchomiony po otrzymaniu żądania HTTP.

## Typy webhooków

W systemie Morris możemy wyróżnić następujące typy webhooków:

### Webhooks wejściowe (Inbound)

- Otrzymują żądania HTTP od systemów zewnętrznych
- Uruchamiają zdefiniowane łańcuchy przetwarzania
- Zwracają wyniki przetwarzania jako odpowiedź HTTP
- Dostępne przez endpoint `/hook/<modul>`

### Webhooks wyjściowe (Outbound)

- Wysyłają żądania HTTP do systemów zewnętrznych
- Mogą być uruchamiane jako część łańcucha przetwarzania
- Przekazują dane do zewnętrznych API lub usług
- Implementowane jako elementy łańcucha przetwarzania

## Struktura żądań i odpowiedzi

### Format żądania wejściowego

Żądania HTTP kierowane do webhooków w systemie Morris powinny mieć następującą strukturę:

```http
POST /hook/<modul>
Content-Type: application/json

{
    "action": "nazwa_akcji",
    "data": {
        // Dowolne dane specyficzne dla akcji
        "param1": "wartość1",
        "param2": "wartość2"
    },
    "metadata": {
        "source": "system_źródłowy",
        "timestamp": "2025-04-05T12:34:56Z"
    }
}
```

### Format odpowiedzi

Odpowiedzi z webhooków mają standardową strukturę:

```json
{
    "status": "success|error",
    "message": "Opis wyniku operacji",
    "data": {
        // Dane wynikowe specyficzne dla akcji
    },
    "timestamp": "2025-04-05T12:34:57Z"
}
```

## Rejestracja endpointów

Endpointy webhooków są definiowane w konfiguracji łańcuchów przetwarzania (chains). Każdy łańcuch może być powiązany z określonym endpointem webhookowym.

### Struktura konfiguracji w chains.json

```json
{
    "webhook_chain": {
        "description": "Łańcuch przetwarzania dla przykładowego webhooks",
        "webhook": {
            "endpoint": "przyklad",
            "methods": ["POST"],
            "required_params": ["action", "data"]
        },
        "steps": [
            {
                "name": "walidacja_danych",
                "type": "validator",
                "config": {
                    "schema": {
                        "action": "string",
                        "data": "object"
                    }
                }
            },
            {
                "name": "przetwarzanie",
                "type": "processor",
                "config": {
                    "action_map": {
                        "przyklad_akcji": "przyklad_processor"
                    }
                }
            }
        ]
    }
}
```

## Obsługa webhooków

Obsługa żądań webhookowych przebiega w następujących krokach:

1. Otrzymanie żądania HTTP na endpoint `/hook/<modul>`
2. Identyfikacja odpowiedniego łańcucha przetwarzania na podstawie `<modul>`
3. Walidacja danych wejściowych zgodnie z konfiguracją łańcucha
4. Uruchomienie łańcucha przetwarzania z danymi z żądania
5. Zwrócenie wyniku przetwarzania jako odpowiedzi HTTP

## Bezpieczeństwo

### Uwierzytelnianie

System Morris wspiera różne metody uwierzytelniania dla webhooków:

#### Tokeny API

```http
POST /hook/<modul>
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

{
    // treść żądania
}
```

#### Sekrety webhookowe

```http
POST /hook/<modul>
Content-Type: application/json
X-Webhook-Secret: twoj_sekretny_klucz

{
    // treść żądania
}
```

### Walidacja danych

Zalecane jest stosowanie schematu walidacji dla danych wejściowych w każdym webhooków:

```json
{
    "name": "walidacja_webhooks",
    "type": "validator",
    "config": {
        "schema": {
            "action": {
                "type": "string",
                "required": true
            },
            "data": {
                "type": "object",
                "required": true
            },
            "metadata": {
                "type": "object",
                "required": false
            }
        }
    }
}
```

## Integracja z Chain Engine

Webhooks są ściśle zintegrowane z Chain Engine systemu Morris, co pozwala na:

- Uruchamianie łańcuchów przetwarzania w odpowiedzi na żądania HTTP
- Wykorzystanie wyników przetwarzania łańcucha jako odpowiedzi webhooks
- Automatyczne logowanie i śledzenie żądań webhookowych
- Integrację z systemem powiadamiania i alertów

## Najlepsze praktyki

1. **Walidacja danych wejściowych** - Zawsze weryfikuj format i integralność danych
2. **Uwierzytelnianie** - Stosuj odpowiednie mechanizmy uwierzytelniania dla webhooków
3. **Idempotentność** - Projektuj webhooks tak, aby wielokrotne wywołanie z tymi samymi danymi dawało ten sam rezultat
4. **Obsługa błędów** - Zapewnij czytelne komunikaty błędów z odpowiednimi kodami HTTP
5. **Logowanie** - Rejestruj wszystkie wywołania webhooków z odpowiednim poziomem szczegółowości
6. **Limity czasowe** - Ustaw rozsądne limity czasowe dla przetwarzania żądań webhookowych
7. **Ograniczenie częstotliwości** - Implementuj mechanizmy rate-limitingu dla publicznych endpointów
8. **Używaj skryptu zarządzającego** - Do uruchamiania i zatrzymywania aplikacji Morris wraz z jej webhookami używaj skryptu `morris.py` (dostępnego w głównym katalogu projektu), który zapewnia prawidłowe zarządzanie procesami głównymi i potomnymi:
   ```bash
   # Uruchamianie
   python morris.py start
   
   # Zatrzymywanie
   python morris.py stop
   
   # Sprawdzanie statusu
   python morris.py status
   
   # Restart
   python morris.py restart
   ```

## Przykłady

### Przykład prostego webhooks do przetwarzania danych

#### Konfiguracja w chains.json

```json
{
    "data_processing_chain": {
        "description": "Łańcuch przetwarzania danych z zewnętrznych źródeł",
        "webhook": {
            "endpoint": "process_data",
            "methods": ["POST"],
            "required_params": ["data_type", "content"]
        },
        "steps": [
            {
                "name": "walidacja",
                "type": "validator",
                "config": {
                    "schema": {
                        "data_type": {
                            "type": "string",
                            "enum": ["text", "json", "csv"]
                        },
                        "content": {
                            "type": "string",
                            "minLength": 1
                        }
                    }
                }
            },
            {
                "name": "konwersja_danych",
                "type": "data_converter",
                "config": {
                    "type_map": {
                        "text": "text_processor",
                        "json": "json_processor",
                        "csv": "csv_processor"
                    }
                }
            },
            {
                "name": "analiza",
                "type": "data_analyzer",
                "config": {
                    "analysis_types": ["summary", "sentiment", "keywords"]
                }
            }
        ],
        "output": {
            "format": "json",
            "fields": ["summary", "sentiment", "keywords"]
        }
    }
}
```

#### Przykładowe żądanie

```http
POST /hook/process_data
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

{
    "data_type": "text",
    "content": "Morris to zaawansowany system integracji i przetwarzania danych wykorzystujący nowoczesne technologie.",
    "metadata": {
        "source": "przykladowa_aplikacja",
        "timestamp": "2025-04-05T12:00:00Z"
    }
}
```

#### Przykładowa odpowiedź

```json
{
    "status": "success",
    "message": "Dane przetworzone pomyślnie",
    "data": {
        "summary": "Tekst opisuje system Morris do integracji i przetwarzania danych.",
        "sentiment": {
            "score": 0.72,
            "label": "positive"
        },
        "keywords": ["Morris", "system", "integracja", "przetwarzanie danych", "technologie"]
    },
    "timestamp": "2025-04-05T12:00:01Z"
}
```

### Przykład webhooks do integracji z zewnętrznym systemem powiadomień

#### Konfiguracja w chains.json

```json
{
    "notification_chain": {
        "description": "Łańcuch do obsługi powiadomień z zewnętrznych systemów",
        "webhook": {
            "endpoint": "notification",
            "methods": ["POST"],
            "required_params": ["type", "message"]
        },
        "steps": [
            {
                "name": "walidacja_powiadomienia",
                "type": "validator",
                "config": {
                    "schema": {
                        "type": {
                            "type": "string",
                            "enum": ["info", "warning", "alert", "critical"]
                        },
                        "message": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 500
                        },
                        "target": {
                            "type": "string",
                            "required": false
                        }
                    }
                }
            },
            {
                "name": "klasyfikacja_powiadomienia",
                "type": "classifier",
                "config": {
                    "type_map": {
                        "info": "low_priority",
                        "warning": "medium_priority",
                        "alert": "high_priority",
                        "critical": "immediate_action"
                    }
                }
            },
            {
                "name": "routing_powiadomienia",
                "type": "router",
                "config": {
                    "routes": {
                        "low_priority": "log_only",
                        "medium_priority": "notify_system",
                        "high_priority": "notify_admin",
                        "immediate_action": "alert_team"
                    }
                }
            },
            {
                "name": "wysylanie_powiadomienia",
                "type": "notifier",
                "config": {
                    "channels": {
                        "log_only": {"type": "log", "level": "info"},
                        "notify_system": {"type": "mqtt", "topic": "system/notifications"},
                        "notify_admin": {"type": "email", "template": "admin_alert"},
                        "alert_team": {"type": "sms", "template": "emergency_alert"}
                    }
                }
            }
        ],
        "output": {
            "format": "json",
            "fields": ["notification_id", "status", "delivery_info"]
        }
    }
}
```

#### Przykładowe żądanie

```http
POST /hook/notification
Content-Type: application/json
X-Webhook-Secret: tajny_klucz_webhook

{
    "type": "alert",
    "message": "Wykryto wysokie zużycie CPU na serwerze aplikacyjnym",
    "target": "admin",
    "metadata": {
        "source": "monitoring_system",
        "server": "app-server-01",
        "cpu_usage": 95.2,
        "timestamp": "2025-04-05T13:15:22Z"
    }
}
```

#### Przykładowa odpowiedź

```json
{
    "status": "success",
    "message": "Powiadomienie zostało przetworzone",
    "data": {
        "notification_id": "notif-2025040513152201",
        "status": "sent",
        "delivery_info": {
            "channel": "email",
            "recipient": "admin@przykład.pl",
            "sent_at": "2025-04-05T13:15:23Z"
        }
    },
    "timestamp": "2025-04-05T13:15:23Z"
}
```

## Implementacja własnego handlera webhooks

Oto przykład implementacji własnego handlera do obsługi webhooków w Pythonie z użyciem Flask:

```python
from flask import Blueprint, request, jsonify, current_app
import json
import logging
from datetime import datetime

# Konfiguracja loggera
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Utworzenie blueprintu dla webhooków
webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/hook/<modul>', methods=['POST'])
def handle_webhook(modul):
    """
    Główny endpoint do obsługi webhooków.
    
    Args:
        modul (str): Identyfikator modułu/chainu do wywołania
        
    Returns:
        Response: Wynik przetwarzania w formacie JSON
    """
    # Sprawdzenie czy żądanie zawiera JSON
    if not request.is_json:
        logger.warning(f"Otrzymano nieprawidłowe żądanie dla webhooks /{modul} (brak JSON)")
        return jsonify({
            "status": "error",
            "message": "Oczekiwano danych w formacie JSON",
            "timestamp": datetime.now().isoformat()
        }), 400
    
    # Pobranie danych z żądania
    webhook_data = request.get_json()
    
    # Pobranie chain engine z kontekstu aplikacji
    chain_engine = current_app.config.get('chain_engine')
    
    if not chain_engine:
        logger.error("Chain Engine nie jest dostępny w kontekście aplikacji")
        return jsonify({
            "status": "error",
            "message": "Błąd konfiguracji serwera",
            "timestamp": datetime.now().isoformat()
        }), 500
    
    # Sprawdzenie czy istnieje chain dla danego modułu
    if not chain_engine.has_chain(modul):
        logger.warning(f"Nie znaleziono łańcucha dla modułu: {modul}")
        return jsonify({
            "status": "error",
            "message": f"Nie znaleziono obsługi dla modułu: {modul}",
            "timestamp": datetime.now().isoformat()
        }), 404
    
    try:
        # Uruchomienie chainu z danymi z webhooks
        logger.info(f"Uruchamianie chainu dla webhooks /{modul}")
        result = chain_engine.run_chain(modul, webhook_data)
        
        # Zwrócenie wyniku przetwarzania
        return jsonify({
            "status": "success",
            "message": f"Webhook {modul} przetworzony pomyślnie",
            "data": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Błąd podczas przetwarzania webhooks /{modul}: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Wystąpił błąd podczas przetwarzania: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500
```

---

## Podsumowanie

Webhooks w systemie Morris stanowią elastyczny mechanizm integracji z zewnętrznymi systemami, umożliwiając przetwarzanie danych przychodzących przez HTTP oraz uruchamianie zdefiniowanych łańcuchów przetwarzania. Przestrzeganie powyższych wytycznych zapewni spójność i niezawodność działania webhooków w całym systemie.

Przy tworzeniu i korzystaniu z webhooków:
1. Definiuj jasną strukturę danych wejściowych i wyjściowych
2. Implementuj odpowiednie mechanizmy uwierzytelniania i walidacji
3. Projektuj webhooks zgodnie z zasadami RESTful API
4. Integruj webhooks z łańcuchami przetwarzania w sposób modułowy i elastyczny

Więcej informacji i pomoc można znaleźć w głównej dokumentacji systemu Morris lub w kodzie źródłowym modułu obsługi webhooków.

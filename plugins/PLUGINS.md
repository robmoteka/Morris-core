# Tworzenie wtyczek dla systemu Morris

Ten dokument zawiera wytyczne dla modeli językowych (LLM) dotyczące tworzenia nowych wtyczek kompatybilnych z systemem Morris. Znajdziesz tu instrukcje, przykłady i najlepsze praktyki, które pomogą w spójnym tworzeniu nowych komponentów rozszerzających funkcjonalność systemu.

## Spis treści

1. [Architektura wtyczek](#architektura-wtyczek)
2. [Typy wtyczek](#typy-wtyczek)
3. [Wymagane metadane](#wymagane-metadane)
4. [Sposoby rejestracji wtyczek](#sposoby-rejestracji-wtyczek)
5. [Cykl życia wtyczki](#cykl-życia-wtyczki)
6. [Implementacja wtyczek](#implementacja-wtyczek)
   - [Wtyczki lokalne](#wtyczki-lokalne)
   - [Wtyczki MQTT](#wtyczki-mqtt)
   - [Wtyczki REST](#wtyczki-rest)
7. [Najlepsze praktyki](#najlepsze-praktyki)
8. [Przykłady](#przykłady)

## Architektura wtyczek

System Morris wykorzystuje architekturę wtyczek do rozszerzania swoich możliwości. Plugin Manager odpowiada za:

- Rejestrację wtyczek (lokalnych i zdalnych)
- Śledzenie statusu wtyczek
- Dostarczanie API do zarządzania wtyczkami
- Integrację z Chain Engine do wywoływania wtyczek

Wtyczki dzielą się na 3 główne typy: lokalne, MQTT i REST, w zależności od sposobu komunikacji i integracji z systemem.

## Typy wtyczek

### Wtyczki lokalne

- Wykonywane bezpośrednio w procesie głównym Morris
- Implementowane jako moduły Pythona
- Najszybsze pod względem wydajności
- Idealne dla podstawowych funkcjonalności i operacji wymagających niskiego opóźnienia

### Wtyczki MQTT

- Komunikują się z Morris przez protokół MQTT
- Mogą działać na zdalnych systemach
- Umożliwiają rozproszenie obciążenia
- Dobre dla zadań wymagających dużych zasobów obliczeniowych lub specjalistycznych bibliotek

### Wtyczki REST

- Komunikują się z Morris przez API REST
- Łatwe do integracji z istniejącymi systemami
- Mogą być zaimplementowane w dowolnym języku programowania
- Idealne dla integracji z zewnętrznymi usługami lub systemami

## Wymagane metadane

Każda wtyczka musi posiadać następujące metadane:

| Pole | Typ | Opis | Wymagane |
|------|-----|------|----------|
| `name` | string | Unikalna nazwa wtyczki | Tak |
| `type` | string | Typ wtyczki: `local`, `mqtt` lub `rest` | Tak |
| `description` | string | Krótki opis funkcjonalności wtyczki | Tak |
| `status` | string | Status wtyczki: `online` lub `offline` | Tak |
| `last_seen` | string (ISO datetime) | Czas ostatniego kontaktu z wtyczką | Opcjonalnie (dodawane automatycznie) |
| `version` | string | Wersja wtyczki (zalecany format: semver) | Opcjonalnie |
| `author` | string | Autor wtyczki | Opcjonalnie |
| `config` | object | Konfiguracja specyficzna dla wtyczki | Opcjonalnie |

## Sposoby rejestracji wtyczek

### Rejestracja przez REST API

Wtyczki mogą być rejestrowane przez wysłanie żądania POST na endpoint `/api/plugins`:

```http
POST /api/plugins
Content-Type: application/json

{
    "name": "nazwa_wtyczki",
    "type": "mqtt",
    "description": "Opis funkcjonalności wtyczki",
    "status": "online"
}
```

### Rejestracja przez MQTT

Wtyczki mogą automatycznie rejestrować się przez wysłanie wiadomości na temat `plugin/announce`:

```json
{
    "name": "nazwa_wtyczki",
    "type": "mqtt",
    "description": "Opis funkcjonalności wtyczki",
    "status": "online"
}
```

### Rejestracja wtyczek lokalnych

Wtyczki lokalne powinny być rejestrowane podczas inicjalizacji aplikacji poprzez wywołanie metody `register_plugin()` klasy `PluginManager`:

```python
plugin_manager.register_plugin({
    "name": "nazwa_wtyczki",
    "type": "local",
    "description": "Opis funkcjonalności wtyczki",
    "status": "online"
})
```

## Cykl życia wtyczki

1. **Rejestracja** - Wtyczka rejestruje się w systemie, podając swoje metadane
2. **Aktywność** - Wtyczka regularnie wysyła ogłoszenia (dla typu MQTT) lub odpowiada na wywołania (dla typu REST)
3. **Monitorowanie** - Plugin Manager śledzi status wtyczki i oznacza ją jako `offline`, jeśli nie kontaktuje się przez dłuższy czas (domyślnie 60s)
4. **Wyrejestrowanie** - Wtyczka może być usunięta z rejestru przez endpoint DELETE lub przez wywołanie metody `unregister_plugin()`

## Implementacja wtyczek

### Wtyczki lokalne

Przykładowy schemat implementacji wtyczki lokalnej:

```python
class MojWtyczkaLokalna:
    def __init__(self):
        self.name = "moja_wtyczka"
        self.type = "local"
        self.description = "Moja testowa wtyczka lokalna"
        
    def register(self, plugin_manager):
        """Rejestruje wtyczkę w Plugin Manager."""
        return plugin_manager.register_plugin({
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "status": "online"
        })
        
    def process(self, input_data):
        """Przetwarza dane wejściowe i zwraca wynik."""
        # Logika przetwarzania
        result = {"output": "przetworzone dane"}
        return result
```

### Wtyczki MQTT

Przykładowy schemat implementacji wtyczki MQTT:

```python
import json
import paho.mqtt.client as mqtt
import time
from datetime import datetime

class MojWtyczkaMQTT:
    def __init__(self, broker="broker.emqx.io", port=1883):
        self.name = "moja_wtyczka_mqtt"
        self.type = "mqtt"
        self.description = "Moja testowa wtyczka MQTT"
        self.client = mqtt.Client()
        self.broker = broker
        self.port = port
        
        # Konfiguracja callbacków
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
    def start(self):
        """Uruchamia wtyczkę i łączy z brokerem MQTT."""
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()
        
        # Regularne ogłaszanie obecności
        while True:
            self.announce()
            time.sleep(30)  # Ogłaszanie co 30 sekund
            
    def announce(self):
        """Wysyła ogłoszenie o obecności wtyczki."""
        announcement = {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "status": "online",
            "timestamp": datetime.now().isoformat()
        }
        self.client.publish("plugin/announce", json.dumps(announcement))
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback wywoływany po połączeniu z brokerem."""
        print(f"Połączono z kodem {rc}")
        # Subskrybuj tematy dla tej wtyczki
        client.subscribe(f"plugin/{self.name}/request")
        
    def on_message(self, client, userdata, msg):
        """Callback wywoływany po otrzymaniu wiadomości."""
        if msg.topic == f"plugin/{self.name}/request":
            # Przetwarzanie żądania
            try:
                request = json.loads(msg.payload.decode())
                result = self.process(request)
                # Publikacja odpowiedzi
                self.client.publish(f"plugin/{self.name}/response", json.dumps(result))
            except Exception as e:
                error = {"error": str(e)}
                self.client.publish(f"plugin/{self.name}/response", json.dumps(error))
                
    def process(self, input_data):
        """Przetwarza dane wejściowe i zwraca wynik."""
        # Logika przetwarzania
        result = {"output": "przetworzone dane"}
        return result

# Użycie
if __name__ == "__main__":
    plugin = MojWtyczkaMQTT()
    plugin.start()
```

### Wtyczki REST

Przykładowy schemat implementacji wtyczki REST (używając Flask):

```python
from flask import Flask, request, jsonify
import requests
import json
import threading
import time
from datetime import datetime

app = Flask(__name__)
MORRIS_API = "http://localhost:5010"  # Adres API Morris

class MojWtyczkaREST:
    def __init__(self, host="0.0.0.0", port=5050):
        self.name = "moja_wtyczka_rest"
        self.type = "rest"
        self.description = "Moja testowa wtyczka REST"
        self.host = host
        self.port = port
        
    def start(self):
        """Uruchamia serwer Flask i rejestruje wtyczkę."""
        # Uruchomienie wątku ogłoszeń
        threading.Thread(target=self.announcement_loop, daemon=True).start()
        # Uruchomienie serwera Flask
        app.run(host=self.host, port=self.port)
        
    def register(self):
        """Rejestruje wtyczkę w systemie Morris."""
        plugin_data = {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "status": "online"
        }
        try:
            response = requests.post(f"{MORRIS_API}/api/plugins", json=plugin_data)
            return response.status_code == 201
        except Exception as e:
            print(f"Błąd rejestracji: {e}")
            return False
            
    def announcement_loop(self):
        """Okresowo wysyła ogłoszenia o obecności wtyczki."""
        while True:
            self.register()
            time.sleep(30)  # Ogłaszanie co 30 sekund
            
    def process(self, input_data):
        """Przetwarza dane wejściowe i zwraca wynik."""
        # Logika przetwarzania
        result = {"output": "przetworzone dane"}
        return result

# Endpoint do przetwarzania żądań
@app.route("/api/process", methods=["POST"])
def process_request():
    plugin = app.config["plugin"]
    if not request.is_json:
        return jsonify({"error": "Oczekiwano danych JSON"}), 400
    
    input_data = request.get_json()
    result = plugin.process(input_data)
    return jsonify(result)

# Użycie
if __name__ == "__main__":
    plugin = MojWtyczkaREST()
    app.config["plugin"] = plugin
    plugin.start()
```

## Najlepsze praktyki

1. **Unikalne nazwy** - Używaj unikalnych, opisowych nazw dla wtyczek
2. **Regularne ogłoszenia** - Wtyczki MQTT powinny regularnie ogłaszać swoją obecność (co 30-45 sekund)
3. **Obsługa błędów** - Implementuj odpowiednią obsługę błędów i zwracaj informacyjne komunikaty
4. **Wersjonowanie** - Użyj pola `version` do śledzenia wersji wtyczki
5. **Dokumentacja** - Dołącz dokładny opis funkcjonalności i parametrów wtyczki
6. **Logowanie** - Używaj logowania do śledzenia działania wtyczki
7. **Graceful shutdown** - Obsługuj poprawne zamykanie wtyczki i wyrejestrowanie
8. **Używaj skryptu zarządzającego** - Do uruchamiania i zatrzymywania aplikacji Morris wraz z jej wtyczkami używaj skryptu `morris.py` (dostępnego w głównym katalogu projektu), który zapewnia prawidłowe zarządzanie procesami głównymi i potomnymi:
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

### Przykład prostej wtyczki lokalnej do obliczania statystyk

```python
class StatisticsPlugin:
    def __init__(self):
        self.name = "statistics_calculator"
        self.type = "local"
        self.description = "Oblicza podstawowe statystyki dla dostarczonych danych"
        
    def register(self, plugin_manager):
        return plugin_manager.register_plugin({
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "status": "online",
            "version": "1.0.0",
            "author": "Morris Team"
        })
        
    def calculate(self, data):
        """
        Oblicza statystyki dla listy liczb.
        
        Args:
            data (list): Lista liczb
            
        Returns:
            dict: Obliczone statystyki
        """
        if not data or not isinstance(data, list):
            return {"error": "Wymagana jest niepusta lista liczb"}
            
        try:
            numbers = [float(n) for n in data]
            n = len(numbers)
            total = sum(numbers)
            mean = total / n
            sorted_nums = sorted(numbers)
            
            if n % 2 == 0:
                median = (sorted_nums[n//2 - 1] + sorted_nums[n//2]) / 2
            else:
                median = sorted_nums[n//2]
                
            variance = sum((x - mean) ** 2 for x in numbers) / n
            std_dev = variance ** 0.5
            
            return {
                "count": n,
                "sum": total,
                "mean": mean,
                "median": median,
                "min": min(numbers),
                "max": max(numbers),
                "variance": variance,
                "std_deviation": std_dev
            }
        except Exception as e:
            return {"error": f"Błąd podczas obliczania statystyk: {str(e)}"}
```

### Przykład wtyczki MQTT do monitorowania temperatury

```python
import json
import paho.mqtt.client as mqtt
import time
import random
from datetime import datetime

class TemperatureMonitorPlugin:
    def __init__(self, broker="broker.emqx.io", port=1883):
        self.name = "temperature_monitor"
        self.type = "mqtt"
        self.description = "Monitoruje temperaturę i wysyła powiadomienia przy przekroczeniu progów"
        self.client = mqtt.Client()
        self.broker = broker
        self.port = port
        self.thresholds = {"low": 18.0, "high": 28.0}
        
        # Konfiguracja callbacków
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
    def start(self):
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()
        
        # Symulacja odczytów temperatury
        while True:
            temperature = self.simulate_temperature()
            self.publish_temperature(temperature)
            self.announce()
            time.sleep(30)
            
    def simulate_temperature(self):
        """Symuluje odczyt temperatury."""
        return round(random.uniform(15.0, 32.0), 1)
        
    def publish_temperature(self, temperature):
        """Publikuje odczyt temperatury i sprawdza progi."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "value": temperature,
            "unit": "C"
        }
        
        self.client.publish(f"sensor/temperature", json.dumps(data))
        
        # Sprawdzenie progów
        if temperature < self.thresholds["low"]:
            alert = {
                "type": "alert",
                "level": "warning",
                "message": f"Temperatura poniżej progu: {temperature}°C (próg: {self.thresholds['low']}°C)"
            }
            self.client.publish(f"alert/temperature", json.dumps(alert))
        elif temperature > self.thresholds["high"]:
            alert = {
                "type": "alert",
                "level": "warning",
                "message": f"Temperatura powyżej progu: {temperature}°C (próg: {self.thresholds['high']}°C)"
            }
            self.client.publish(f"alert/temperature", json.dumps(alert))
            
    def announce(self):
        """Wysyła ogłoszenie o obecności wtyczki."""
        announcement = {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "config": {
                "thresholds": self.thresholds
            }
        }
        self.client.publish("plugin/announce", json.dumps(announcement))
        
    def on_connect(self, client, userdata, flags, rc):
        print(f"Połączono z kodem {rc}")
        # Subskrybuj tematy konfiguracyjne
        client.subscribe(f"plugin/{self.name}/config")
        
    def on_message(self, client, userdata, msg):
        if msg.topic == f"plugin/{self.name}/config":
            try:
                config = json.loads(msg.payload.decode())
                if "thresholds" in config:
                    self.thresholds.update(config["thresholds"])
                    print(f"Zaktualizowano progi: {self.thresholds}")
            except Exception as e:
                print(f"Błąd aktualizacji konfiguracji: {e}")

# Użycie
if __name__ == "__main__":
    plugin = TemperatureMonitorPlugin()
    plugin.start()
```

---

## Podsumowanie

Tworzenie wtyczek dla systemu Morris jest elastyczne i umożliwia implementację w różnych technologiach. Przestrzeganie powyższych wytycznych zapewni spójność i niezawodność działania wtyczek w całym systemie.

Przy tworzeniu nowych wtyczek:
1. Wybierz odpowiedni typ (lokalny, MQTT, REST) w zależności od wymagań
2. Zaimplementuj wszystkie wymagane metadane
3. Zapewnij regularne ogłoszenia obecności (dla wtyczek zdalnych)
4. Stosuj się do najlepszych praktyk opisanych w tym dokumencie

Więcej informacji i pomoc można znaleźć w głównej dokumentacji systemu Morris lub w kodzie źródłowym [Plugin Managera](plugins/manager.py).

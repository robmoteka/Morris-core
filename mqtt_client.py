import json
import logging
import threading
import time
import paho.mqtt.client as mqtt_client
import random
import string

# Konfiguracja loggera
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MqttClient:
    """
    Klasa obsługująca komunikację MQTT dla aplikacji Morris.
    Działa w osobnym wątku i obsługuje połączenie, subskrypcję i publikację wiadomości.
    """
    
    def __init__(self, config_path="config/mqtt.json"):
        """
        Inicjalizacja klienta MQTT.
        
        Args:
            config_path (str): Ścieżka do pliku konfiguracyjnego MQTT
        """
        self.config = self._load_config(config_path)
        self.client = None
        self.connected = False
        self.thread = None
        self.running = False
        self.chain_engine = None  # Referencja do Chain Engine, ustawiana później
        
        # Generowanie losowego sufiksu dla client_id, aby uniknąć konfliktów
        random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        self.config["client_id"] = f"{self.config['client_id']}_{random_suffix}"
    
    def set_chain_engine(self, chain_engine):
        """
        Ustawia referencję do Chain Engine.
        
        Args:
            chain_engine: Instancja Chain Engine
        """
        self.chain_engine = chain_engine
        logger.info("Ustawiono referencję do Chain Engine w kliencie MQTT")
    
    def _load_config(self, config_path):
        """
        Wczytuje konfigurację MQTT z pliku JSON.
        
        Args:
            config_path (str): Ścieżka do pliku konfiguracyjnego
            
        Returns:
            dict: Słownik z konfiguracją
        """
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Błąd podczas wczytywania konfiguracji MQTT: {e}")
            # Domyślna konfiguracja
            return {
                "broker": "broker.emqx.io",
                "port": 1883,
                "client_id": "morris_core_client",
                "keepalive": 60,
                "topics": {
                    "subscribe": ["core/#"],
                    "publish": "bridge/test/input"
                },
                "username": "",
                "password": ""
            }
    
    def _on_connect(self, client, userdata, flags, rc):
        """
        Callback wywoływany po połączeniu z brokerem MQTT.
        
        Args:
            client: Instancja klienta MQTT
            userdata: Dane użytkownika przekazane do klienta
            flags: Flagi odpowiedzi
            rc: Kod wyniku połączenia
        """
        if rc == 0:
            self.connected = True
            logger.info("Połączono z brokerem MQTT")
            
            # Subskrypcja tematów
            for topic in self.config["topics"]["subscribe"]:
                client.subscribe(topic)
                logger.info(f"Zasubskrybowano temat: {topic}")
        else:
            self.connected = False
            logger.error(f"Nie udało się połączyć z brokerem MQTT, kod błędu: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """
        Callback wywoływany po otrzymaniu wiadomości MQTT.
        
        Args:
            client: Instancja klienta MQTT
            userdata: Dane użytkownika przekazane do klienta
            msg: Otrzymana wiadomość
        """
        try:
            payload = msg.payload.decode()
            logger.info(f"Otrzymano wiadomość z tematu {msg.topic}: {payload}")
            
            # Sprawdzenie, czy wiadomość jest odpowiedzią od zdalnej wtyczki
            if msg.topic.startswith("plugin/") and msg.topic.endswith("/output"):
                # Ta wiadomość zostanie obsłużona przez Chain Engine
                return
            
            # Próba parsowania JSON
            try:
                payloadJson = json.loads(payload)
            except json.JSONDecodeError:
                logger.warning(f"Otrzymana wiadomość nie jest poprawnym JSON: {payload}")
                return
            
            # Sprawdzenie, czy Chain Engine jest dostępny
            if self.chain_engine:
                # Utworzenie triggera dla Chain Engine
                triggerId = f"mqtt:{msg.topic}"
                
                # Sprawdzenie, czy istnieje chain dla tego triggera
                chainId, chain = self.chain_engine.get_chain_for_trigger(triggerId)
                
                if chainId:
                    logger.info(f"Znaleziono chain '{chainId}' dla triggera '{triggerId}'. Uruchamianie...")
                    
                    # Uruchomienie chaina asynchronicznie
                    def on_chain_complete(result):
                        logger.info(f"Chain '{chainId}' zakończył przetwarzanie. Wynik: {result}")
                    
                    self.chain_engine.run_chain_async(triggerId, payloadJson, on_chain_complete)
                else:
                    logger.debug(f"Nie znaleziono chaina dla triggera '{triggerId}'. Wiadomość została tylko zalogowana.")
            
        except Exception as e:
            logger.error(f"Błąd podczas przetwarzania wiadomości MQTT: {e}")
    
    def _on_disconnect(self, client, userdata, rc):
        """
        Callback wywoływany po rozłączeniu z brokerem MQTT.
        
        Args:
            client: Instancja klienta MQTT
            userdata: Dane użytkownika przekazane do klienta
            rc: Kod wyniku rozłączenia
        """
        self.connected = False
        if rc != 0:
            logger.warning(f"Nieoczekiwane rozłączenie z brokerem MQTT, kod: {rc}")
            # Próba ponownego połączenia zostanie obsłużona przez automatic reconnect
        else:
            logger.info("Rozłączono z brokerem MQTT")
    
    def start(self):
        """
        Uruchamia klienta MQTT w osobnym wątku.
        """
        if self.thread and self.thread.is_alive():
            logger.warning("Klient MQTT już działa")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_client_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Uruchomiono klienta MQTT w osobnym wątku")
    
    def _run_client_loop(self):
        """
        Główna pętla klienta MQTT uruchamiana w osobnym wątku.
        """
        try:
            # Utworzenie nowego klienta z protokołem v3.1
            self.client = mqtt_client.Client(client_id=self.config["client_id"], protocol=mqtt_client.MQTTv31)
            
            # Włączenie automatycznego ponownego łączenia
            self.client.reconnect_delay_set(min_delay=1, max_delay=120)
            
            # Ustawienie callbacków
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_disconnect = self._on_disconnect
            
            # Ustawienie autoryzacji, jeśli podano dane
            if self.config.get("username") and self.config.get("password"):
                self.client.username_pw_set(self.config["username"], self.config["password"])
            
            # Połączenie z brokerem
            logger.info(f"Próba połączenia z brokerem MQTT: {self.config['broker']}:{self.config['port']}")
            self.client.connect(
                self.config["broker"],
                self.config["port"],
                self.config["keepalive"]
            )
            
            # Uruchomienie pętli klienta
            self.client.loop_start()
            
            # Pętla sprawdzająca stan klienta
            while self.running:
                time.sleep(1)
            
            # Zatrzymanie pętli klienta
            self.client.loop_stop()
            
            # Rozłączenie z brokerem
            if self.connected:
                self.client.disconnect()
                
        except Exception as e:
            logger.error(f"Błąd w pętli klienta MQTT: {e}")
            self.running = False
    
    def stop(self):
        """
        Zatrzymuje klienta MQTT.
        """
        if not self.running:
            logger.warning("Klient MQTT nie jest uruchomiony")
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        
        if self.client and self.connected:
            self.client.disconnect()
        
        logger.info("Zatrzymano klienta MQTT")
    
    def publish(self, topic=None, payload=None, qos=0, retain=False):
        """
        Publikuje wiadomość MQTT.
        
        Args:
            topic (str, optional): Temat, na który ma zostać opublikowana wiadomość.
                                   Jeśli nie podano, używany jest domyślny temat z konfiguracji.
            payload (str/dict, optional): Treść wiadomości. Jeśli podano słownik, zostanie on
                                          przekonwertowany do formatu JSON.
            qos (int, optional): Poziom QoS (0, 1 lub 2). Domyślnie 0.
            retain (bool, optional): Czy wiadomość ma być zachowana przez broker. Domyślnie False.
            
        Returns:
            bool: True jeśli publikacja się powiodła, False w przeciwnym wypadku
        """
        # Jeśli klient nie jest połączony, spróbuj ponownie połączyć
        if not self.client or not self.connected:
            logger.warning("Nie można opublikować wiadomości - klient MQTT nie jest połączony")
            # Zwróć False, ale nie generuj błędu - aplikacja może działać bez MQTT
            return False
        
        # Użyj domyślnego tematu, jeśli nie podano
        if topic is None:
            topic = self.config["topics"]["publish"]
        
        # Konwersja słownika do JSON
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        
        try:
            result = self.client.publish(topic, payload, qos, retain)
            if result.rc == 0:
                logger.info(f"Opublikowano wiadomość na temat {topic}: {payload}")
                return True
            else:
                logger.error(f"Nie udało się opublikować wiadomości, kod błędu: {result.rc}")
                return False
        except Exception as e:
            logger.error(f"Błąd podczas publikacji wiadomości MQTT: {e}")
            return False

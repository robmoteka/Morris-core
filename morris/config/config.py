import os
import logging

class Config:
    """Klasa bazowa konfiguracji aplikacji"""
    # Wersja aplikacji
    VERSION = "0.0.3"
    
    # Konfiguracja Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'morris-secret-key-change-in-production'
    DEBUG = False
    
    # Ścieżki do plików danych
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    PLUGINS_FILE = os.path.join(DATA_DIR, 'plugins.json')
    CHAINS_FILE = os.path.join(DATA_DIR, 'chains.json')
    
    # Konfiguracja MQTT
    MQTT_BROKER_URL = os.environ.get('MQTT_BROKER_URL') or 'localhost'
    MQTT_BROKER_PORT = int(os.environ.get('MQTT_BROKER_PORT') or 1883)
    MQTT_USERNAME = os.environ.get('MQTT_USERNAME') or ''
    MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD') or ''
    MQTT_KEEPALIVE = int(os.environ.get('MQTT_KEEPALIVE') or 60)
    
    # Konfiguracja logowania
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = os.path.join(BASE_DIR, 'morris.log')


class DevelopmentConfig(Config):
    """Konfiguracja dla środowiska deweloperskiego"""
    DEBUG = True
    LOG_LEVEL = logging.DEBUG


class ProductionConfig(Config):
    """Konfiguracja dla środowiska produkcyjnego"""
    DEBUG = False
    
    # W produkcji należy ustawić bezpieczny klucz
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'bardzo-trudny-do-zgadniecia-klucz'


class TestingConfig(Config):
    """Konfiguracja dla środowiska testowego"""
    TESTING = True
    DEBUG = True
    
    # Używamy plików tymczasowych dla testów
    import tempfile
    DATA_DIR = tempfile.mkdtemp()
    PLUGINS_FILE = os.path.join(DATA_DIR, 'plugins.json')
    CHAINS_FILE = os.path.join(DATA_DIR, 'chains.json')


# Słownik konfiguracji dla różnych środowisk
config_by_name = {
    'dev': DevelopmentConfig,
    'prod': ProductionConfig,
    'test': TestingConfig
}

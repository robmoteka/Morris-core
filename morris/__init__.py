"""
Morris Core - Główny moduł aplikacji
"""
import os
import logging
from flask import Flask

from morris.config.config import config_by_name

# Konfiguracja loggera
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def create_app(config_name='dev'):
    """
    Fabryka aplikacji Flask
    
    Args:
        config_name (str): Nazwa konfiguracji (dev, prod, test)
        
    Returns:
        Flask: Skonfigurowana instancja aplikacji Flask
    """
    app = Flask(__name__, 
                template_folder='web/templates',
                static_folder='web/static')
    
    # Wczytaj konfigurację
    config_obj = config_by_name.get(config_name, config_by_name['dev'])
    app.config.from_object(config_obj)
    
    # Upewnij się, że katalog danych istnieje
    os.makedirs(app.config['DATA_DIR'], exist_ok=True)
    
    # Konfiguracja loggera
    logging.basicConfig(
        level=app.config['LOG_LEVEL'],
        format=app.config['LOG_FORMAT'],
        filename=app.config['LOG_FILE']
    )
    
    # Inicjalizacja komponentów
    from morris.core.plugins.manager import PluginManager
    from morris.core.chains.engine import ChainEngine
    from morris.core.mqtt.client import MqttClient
    
    # Inicjalizacja menedżera pluginów
    plugin_manager = PluginManager(app)
    app.plugin_manager = plugin_manager
    
    # Inicjalizacja silnika łańcuchów
    chain_engine = ChainEngine(app, plugin_manager)
    app.chain_engine = chain_engine
    
    # Inicjalizacja klienta MQTT
    mqtt_client = MqttClient(app, chain_engine)
    app.mqtt_client = mqtt_client
    
    # Rejestracja blueprintów
    from morris.web.routes.pages import pages_bp
    from morris.web.routes.chains import chains_bp
    from morris.web.routes.plugins import plugins_bp
    from morris.api.v1.plugins import plugins_api_bp
    from morris.web.routes.webhook import webhook_bp
    
    app.register_blueprint(pages_bp)
    app.register_blueprint(chains_bp, url_prefix='/chains')
    app.register_blueprint(plugins_bp, url_prefix='/plugins')
    app.register_blueprint(plugins_api_bp, url_prefix='/api/v1/plugins')
    app.register_blueprint(webhook_bp, url_prefix='/webhook')
    
    # Konfiguracja obsługi błędów
    from morris.web.routes.errors import register_error_handlers
    register_error_handlers(app)
    
    return app
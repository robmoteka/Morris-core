from flask import Flask, jsonify, request
import logging
import json
import os
from datetime import datetime
from routes.webhook import webhook_bp
from api.plugins import plugins_bp
from mqtt_client import MqttClient
from core.chain_engine import ChainEngine
from plugins.manager import PluginManager

# Import nowych blueprintów dla panelu administracyjnego
from routes.pages import pages_bp
from routes.chains import chains_bp
from routes.plugins import plugins_bp as admin_plugins_bp

# Konfiguracja loggera
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Wersja aplikacji
VERSION = "0.0.2"

# Inicjalizacja aplikacji Flask
app = Flask(__name__)

# Inicjalizacja klienta MQTT
mqtt_client = MqttClient()

# Uruchomienie klienta MQTT przed inicjalizacją Chain Engine
mqtt_client.start()

# Inicjalizacja silnika chainów
chain_engine = ChainEngine(mqtt_client=mqtt_client)

# Inicjalizacja managera wtyczek
plugin_manager = PluginManager(mqtt_client=mqtt_client)

# Dodanie Chain Engine i Plugin Manager do kontekstu aplikacji
app.config["chain_engine"] = chain_engine
app.config["plugin_manager"] = plugin_manager


# Konfiguracja kontekstu dla szablonów
@app.context_processor
def inject_logo():
    """
    Funkcja wstrzykująca ścieżkę do logo Morris do wszystkich szablonów.

    Returns:
        dict: Słownik z dodatkowymi zmiennymi dla szablonu
    """
    # Sprawdzamy, czy logo istnieje w folderze static/images
    logoPath = "/static/images/morris_dark.png"
    logoFullPath = os.path.join(app.root_path, "static/images/morris_dark.png")

    if os.path.exists(logoFullPath):
        return {"logo_url": logoPath}
    else:
        return {"logo_url": None}


# Rejestracja blueprintów
app.register_blueprint(webhook_bp)
app.register_blueprint(plugins_bp)
# Rejestracja nowych blueprintów dla panelu administracyjnego
app.register_blueprint(pages_bp)
app.register_blueprint(chains_bp)
app.register_blueprint(admin_plugins_bp)


@app.route("/")
def index():
    """
    Strona główna aplikacji.

    Returns:
        Response: Informacja o statusie aplikacji
    """
    return jsonify(
        {
            "status": "running",
            "app": "Morris Core",
            "version": VERSION,
            "endpoints": {
                "webhook": "/hook/<modul>",
                "test_mqtt": "/send-test",
                "chains": "/chains",
                "run_chain": "/run-chain/<chain_id>",
                "plugins": {
                    "list": "/api/plugins",
                    "register": "/api/plugins (POST)",
                    "details": "/api/plugins/<name>",
                },
            },
        }
    )


@app.route("/send-test", methods=["GET"])
def send_test():
    """
    Testowa trasa do publikacji wiadomości MQTT.

    Returns:
        Response: Informacja o statusie publikacji
    """
    # Przykładowe dane testowe
    test_data = {
        "source": "morris_core",
        "action": "test",
        "timestamp": datetime.now().isoformat(),
        "data": {"message": "To jest testowa wiadomość z Morris Core", "value": 42},
    }

    # Publikacja wiadomości
    success = mqtt_client.publish(payload=test_data)

    if success:
        return jsonify(
            {
                "status": "success",
                "message": "Opublikowano testową wiadomość MQTT",
                "data": test_data,
            }
        )
    else:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Nie udało się opublikować wiadomości MQTT",
                }
            ),
            500,
        )


@app.route("/chains", methods=["GET", "POST"])
def manage_chains():
    """
    Zarządzanie chainami.
    GET: Pobiera listę wszystkich chainów.
    POST: Dodaje nowy chain.

    Returns:
        Response: Informacja o statusie operacji
    """
    if request.method == "GET":
        return jsonify({"status": "success", "chains": chain_engine.chains})
    elif request.method == "POST":
        if not request.is_json:
            return (
                jsonify(
                    {"status": "error", "message": "Oczekiwano danych w formacie JSON"}
                ),
                400,
            )

        data = request.get_json()
        chain_id = data.get("chain_id")
        chain_definition = data.get("definition")

        if not chain_id or not chain_definition:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Wymagane pola: chain_id, definition",
                    }
                ),
                400,
            )

        success = chain_engine.add_chain(chain_id, chain_definition)

        if success:
            return jsonify(
                {"status": "success", "message": f"Dodano chain: {chain_id}"}
            )
        else:
            return (
                jsonify({"status": "error", "message": "Nie udało się dodać chaina"}),
                500,
            )


@app.route("/chains/<chain_id>", methods=["GET", "PUT", "DELETE"])
def manage_chain(chain_id):
    """
    Zarządzanie pojedynczym chainem.
    GET: Pobiera definicję chaina.
    PUT: Aktualizuje definicję chaina.
    DELETE: Usuwa chain.

    Args:
        chain_id (str): Identyfikator chaina.

    Returns:
        Response: Informacja o statusie operacji
    """
    if request.method == "GET":
        if chain_id in chain_engine.chains:
            return jsonify(
                {
                    "status": "success",
                    "chain_id": chain_id,
                    "definition": chain_engine.chains[chain_id],
                }
            )
        else:
            return (
                jsonify(
                    {"status": "error", "message": f"Chain {chain_id} nie istnieje"}
                ),
                404,
            )

    elif request.method == "PUT":
        if not request.is_json:
            return (
                jsonify(
                    {"status": "error", "message": "Oczekiwano danych w formacie JSON"}
                ),
                400,
            )

        chain_definition = request.get_json()

        if "trigger" not in chain_definition or "steps" not in chain_definition:
            return (
                jsonify(
                    {"status": "error", "message": "Wymagane pola: trigger, steps"}
                ),
                400,
            )

        success = chain_engine.add_chain(chain_id, chain_definition)

        if success:
            return jsonify(
                {"status": "success", "message": f"Zaktualizowano chain: {chain_id}"}
            )
        else:
            return (
                jsonify(
                    {"status": "error", "message": "Nie udało się zaktualizować chaina"}
                ),
                500,
            )

    elif request.method == "DELETE":
        success = chain_engine.remove_chain(chain_id)

        if success:
            return jsonify(
                {"status": "success", "message": f"Usunięto chain: {chain_id}"}
            )
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Nie udało się usunąć chaina {chain_id}",
                    }
                ),
                404,
            )


@app.route("/run-chain/<chain_id>", methods=["POST"])
def run_chain_manually(chain_id):
    """
    Ręczne uruchomienie chaina.

    Args:
        chain_id (str): Identyfikator chaina do uruchomienia.

    Returns:
        Response: Wynik przetwarzania przez chain
    """
    # Sprawdzenie czy chain istnieje
    if chain_id not in chain_engine.chains:
        return (
            jsonify({"status": "error", "message": f"Chain {chain_id} nie istnieje"}),
            404,
        )

    # Sprawdzenie czy dane przychodzące są w formacie JSON
    if not request.is_json:
        return (
            jsonify(
                {"status": "error", "message": "Oczekiwano danych w formacie JSON"}
            ),
            400,
        )

    # Pobranie danych JSON
    payload = request.get_json()

    # Pobranie triggera dla chaina
    trigger = chain_engine.chains[chain_id].get("trigger", f"manual:{chain_id}")

    try:
        # Uruchomienie chaina
        result = chain_engine.run_chain(trigger, payload)

        return jsonify({"status": "success", "chain_id": chain_id, "result": result})
    except Exception as e:
        logger.error(f"Błąd podczas uruchamiania chaina {chain_id}: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Błąd podczas uruchamiania chaina: {str(e)}",
                }
            ),
            500,
        )


if __name__ == "__main__":
    try:
        # Uruchomienie aplikacji Flask
        logger.info("Uruchamianie aplikacji Morris Core...")
        app.run(host="0.0.0.0", port=30331, debug=True)
    except Exception as e:
        logger.error(f"Błąd podczas uruchamiania aplikacji: {e}")

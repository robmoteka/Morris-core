#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
REST API dla zarządzania wtyczkami w systemie Morris.
Udostępnia endpointy do pobierania listy wtyczek, rejestracji ręcznej
oraz pobierania szczegółów konkretnej wtyczki.
"""

from flask import Blueprint, jsonify, request, current_app
import logging

# Konfiguracja loggera
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Utworzenie blueprintu dla API wtyczek
plugins_bp = Blueprint('plugins_api', __name__)

@plugins_bp.route('/api/plugins', methods=['GET'])
def get_plugins():
    """
    Pobiera listę wszystkich zarejestrowanych wtyczek.
    
    Returns:
        Response: Lista wtyczek w formacie JSON
    """
    # Dostęp do Plugin Managera z kontekstu aplikacji
    plugin_manager = current_app.config.get('plugin_manager')
    
    if not plugin_manager:
        logger.error("Plugin Manager nie jest dostępny w kontekście aplikacji")
        return jsonify({
            "status": "error",
            "message": "Plugin Manager nie jest dostępny"
        }), 500
    
    # Pobranie listy wtyczek
    plugins = plugin_manager.get_plugins()
    
    return jsonify({
        "status": "success",
        "count": len(plugins),
        "plugins": plugins
    })

@plugins_bp.route('/api/plugins', methods=['POST'])
def register_plugin():
    """
    Ręczna rejestracja wtyczki.
    
    Returns:
        Response: Informacja o statusie rejestracji
    """
    # Dostęp do Plugin Managera z kontekstu aplikacji
    plugin_manager = current_app.config.get('plugin_manager')
    
    if not plugin_manager:
        logger.error("Plugin Manager nie jest dostępny w kontekście aplikacji")
        return jsonify({
            "status": "error",
            "message": "Plugin Manager nie jest dostępny"
        }), 500
    
    # Sprawdzenie czy dane przychodzące są w formacie JSON
    if not request.is_json:
        logger.warning("Otrzymano nieprawidłowe dane (nie JSON) dla rejestracji wtyczki")
        return jsonify({
            "status": "error",
            "message": "Oczekiwano danych w formacie JSON"
        }), 400
    
    # Pobranie danych JSON
    plugin_data = request.get_json()
    
    # Sprawdzenie wymaganych pól
    required_fields = ['name', 'type', 'description', 'status']
    missing_fields = [field for field in required_fields if field not in plugin_data]
    
    if missing_fields:
        return jsonify({
            "status": "error",
            "message": f"Brakujące wymagane pola: {', '.join(missing_fields)}"
        }), 400
    
    # Rejestracja wtyczki
    success = plugin_manager.register_plugin(plugin_data)
    
    if success:
        return jsonify({
            "status": "success",
            "message": f"Zarejestrowano wtyczkę: {plugin_data['name']}",
            "plugin": plugin_data
        }), 201
    else:
        return jsonify({
            "status": "error",
            "message": "Nie udało się zarejestrować wtyczki"
        }), 500

@plugins_bp.route('/api/plugins/<n>', methods=['GET'])
def get_plugin(n):
    """
    Pobiera szczegóły konkretnej wtyczki.
    
    Args:
        n (str): Nazwa wtyczki
        
    Returns:
        Response: Szczegóły wtyczki w formacie JSON
    """
    # Dostęp do Plugin Managera z kontekstu aplikacji
    plugin_manager = current_app.config.get('plugin_manager')
    
    if not plugin_manager:
        logger.error("Plugin Manager nie jest dostępny w kontekście aplikacji")
        return jsonify({
            "status": "error",
            "message": "Plugin Manager nie jest dostępny"
        }), 500
    
    # Pobranie danych wtyczki
    plugin = plugin_manager.get_plugin(n)
    
    if plugin:
        return jsonify({
            "status": "success",
            "plugin": plugin
        })
    else:
        return jsonify({
            "status": "error",
            "message": f"Wtyczka {n} nie istnieje"
        }), 404

@plugins_bp.route('/api/plugins/<n>', methods=['DELETE'])
def unregister_plugin(n):
    """
    Usuwa wtyczkę z rejestru.
    
    Args:
        n (str): Nazwa wtyczki do usunięcia
        
    Returns:
        Response: Informacja o statusie operacji
    """
    # Dostęp do Plugin Managera z kontekstu aplikacji
    plugin_manager = current_app.config.get('plugin_manager')
    
    if not plugin_manager:
        logger.error("Plugin Manager nie jest dostępny w kontekście aplikacji")
        return jsonify({
            "status": "error",
            "message": "Plugin Manager nie jest dostępny"
        }), 500
    
    # Usunięcie wtyczki
    success = plugin_manager.unregister_plugin(n)
    
    if success:
        return jsonify({
            "status": "success",
            "message": f"Usunięto wtyczkę: {n}"
        })
    else:
        return jsonify({
            "status": "error",
            "message": f"Nie udało się usunąć wtyczki {n}"
        }), 404

"""
routes/pages.py - Moduł obsługujący podstawowe strony interfejsu administracyjnego

Ten moduł zawiera definicje endpointów do renderowania podstawowych widoków
interfejsu administracyjnego, w tym strony głównej i ogólnej nawigacji.
"""

from flask import Blueprint, render_template, request, redirect, url_for, current_app
import json

# Utworzenie blueprintu dla ścieżek związanych ze stronami statycznymi
pages_bp = Blueprint('pages', __name__)

@pages_bp.route('/')
def index():
    """Strona główna panelu administracyjnego."""
    # Pobierz Chain Engine z kontekstu aplikacji
    chainEngine = current_app.config.get('chain_engine')
    if not chainEngine:
        chainsCount = 0
    else:
        chainsCount = len(chainEngine.chains)
    
    # Pobierz Plugin Manager z kontekstu aplikacji
    pluginManager = current_app.config.get('plugin_manager')
    if not pluginManager:
        pluginsCount = 0
    else:
        plugins = pluginManager.get_plugins()
        pluginsCount = len(plugins)
    
    # Statystyki
    stats = {
        'chainsCount': chainsCount,
        'pluginsCount': pluginsCount,
        'onlinePlugins': 0  # Domyślnie zero, aktualizowane poniżej
    }
    
    # Sprawdź status wtyczek
    if pluginManager:
        for name, plugin in plugins.items():
            if plugin.get('status') == 'online':
                stats['onlinePlugins'] += 1
    
    return render_template('index.html', stats=stats)

@pages_bp.route('/dashboard')
def dashboard():
    """Dashboard z podstawowymi statystykami i stanem systemu."""
    return render_template('dashboard.html')

@pages_bp.route('/settings')
def settings():
    """Strona z ustawieniami systemu."""
    return render_template('settings.html')

@pages_bp.route('/docs')
def documentation():
    """Strona z dokumentacją systemu."""
    return render_template('docs.html')

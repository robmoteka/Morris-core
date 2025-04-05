"""
routes/plugins.py - Moduł obsługujący ścieżki związane z wtyczkami

Ten moduł zawiera definicje endpointów interfejsu webowego do zarządzania wtyczkami,
w tym wyświetlanie listy, dodawanie i usuwanie wtyczek w systemie.
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, current_app
from datetime import datetime
import json

# Utworzenie blueprintu dla ścieżek związanych z wtyczkami
plugins_bp = Blueprint('plugins', __name__)

@plugins_bp.route('/plugins')
def list_plugins():
    """Wyświetla listę wszystkich dostępnych wtyczek."""
    # Pobierz Plugin Manager z kontekstu aplikacji
    pluginManager = current_app.config.get('plugin_manager')
    if not pluginManager:
        flash('Plugin Manager nie jest dostępny', 'danger')
        return render_template('plugins/list.html', plugins=[])
    
    # Pobierz listę wtyczek
    plugins = pluginManager.get_plugins()
    
    # Konwersja słownika na listę dla łatwiejszego wyświetlenia w szablonie
    pluginsList = []
    for name, plugin in plugins.items():
        # Dodaj nazwę do obiektu wtyczki dla wygody
        plugin['name'] = name
        pluginsList.append(plugin)
    
    return render_template('plugins/list.html', plugins=pluginsList)

@plugins_bp.route('/plugins/view/<name>')
def view_plugin(name):
    """
    Wyświetla szczegóły konkretnej wtyczki.
    
    Args:
        name (str): Nazwa wtyczki
    """
    # Pobierz Plugin Manager z kontekstu aplikacji
    pluginManager = current_app.config.get('plugin_manager')
    if not pluginManager:
        flash('Plugin Manager nie jest dostępny', 'danger')
        return redirect(url_for('plugins.list_plugins'))
    
    # Pobierz wtyczkę
    plugin = pluginManager.get_plugin(name)
    if not plugin:
        flash(f'Wtyczka "{name}" nie została znaleziona', 'danger')
        return redirect(url_for('plugins.list_plugins'))
    
    # Dodaj nazwę do obiektu wtyczki dla wygody
    plugin['name'] = name
    
    return render_template('plugins/view.html', plugin=plugin)

@plugins_bp.route('/plugins/register', methods=['POST'])
def register_plugin():
    """Rejestruje nową wtyczkę na podstawie danych z formularza."""
    # Pobierz Plugin Manager z kontekstu aplikacji
    pluginManager = current_app.config.get('plugin_manager')
    if not pluginManager:
        flash('Plugin Manager nie jest dostępny', 'danger')
        return redirect(url_for('plugins.list_plugins'))
    
    # Pobierz dane z formularza
    pluginData = {
        'name': request.form.get('name'),
        'type': request.form.get('type'),
        'description': request.form.get('description'),
        'status': request.form.get('status', 'online')
    }
    
    # Walidacja podstawowych pól
    if not pluginData['name'] or not pluginData['type'] or not pluginData['description']:
        flash('Wszystkie pola są wymagane', 'danger')
        return redirect(url_for('plugins.list_plugins'))
    
    try:
        # Zarejestruj wtyczkę
        result = pluginManager.register_plugin(pluginData)
        
        if result:
            flash(f'Wtyczka "{pluginData["name"]}" została pomyślnie zarejestrowana', 'success')
        else:
            flash(f'Nie udało się zarejestrować wtyczki "{pluginData["name"]}"', 'danger')
    except Exception as e:
        flash(f'Wystąpił błąd podczas rejestracji wtyczki: {str(e)}', 'danger')
    
    return redirect(url_for('plugins.list_plugins'))

@plugins_bp.route('/plugins/unregister/<name>', methods=['POST'])
def unregister_plugin(name):
    """
    Wyrejestrowuje wtyczkę.
    
    Args:
        name (str): Nazwa wtyczki
    """
    # Pobierz Plugin Manager z kontekstu aplikacji
    pluginManager = current_app.config.get('plugin_manager')
    if not pluginManager:
        flash('Plugin Manager nie jest dostępny', 'danger')
        return redirect(url_for('plugins.list_plugins'))
    
    try:
        # Wyrejestruj wtyczkę
        result = pluginManager.unregister_plugin(name)
        
        if result:
            flash(f'Wtyczka "{name}" została pomyślnie wyrejestrowana', 'success')
        else:
            flash(f'Nie udało się wyrejestrować wtyczki "{name}"', 'danger')
    except Exception as e:
        flash(f'Wystąpił błąd podczas wyrejestrowania wtyczki: {str(e)}', 'danger')
    
    return redirect(url_for('plugins.list_plugins'))

# Helper dla formatowania daty i czasu
@plugins_bp.app_template_filter('format_datetime')
def format_datetime(value):
    """
    Formatuje datę i czas dla wyświetlenia w szablonie.
    
    Args:
        value (str): Data i czas w formacie ISO
        
    Returns:
        str: Sformatowana data i czas
    """
    if not value:
        return ''
    
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, AttributeError):
        return value

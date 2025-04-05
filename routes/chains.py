"""
routes/chains.py - Moduł obsługujący ścieżki związane z łańcuchami przetwarzania

Ten moduł zawiera definicje endpointów REST API do zarządzania łańcuchami przetwarzania,
w tym wyświetlanie listy, dodawanie, edycja i usuwanie łańcuchów.
"""

import os
import json
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, current_app
from werkzeug.exceptions import NotFound, BadRequest

# Utworzenie blueprintu dla ścieżek związanych z łańcuchami
chains_bp = Blueprint('chains', __name__)

# Ścieżka do pliku z konfiguracją łańcuchów
CHAINS_FILE = "chains/chains.json"

@chains_bp.route('/chains')
def list_chains():
    """Wyświetla listę wszystkich dostępnych łańcuchów przetwarzania."""
    chains = load_chains()
    return render_template('chains/list.html', chains=chains)

@chains_bp.route('/chains/new', methods=['GET'])
def new_chain():
    """Wyświetla formularz do tworzenia nowego łańcucha."""
    # Pobierz informacje o dostępnych pluginach
    plugin_manager = current_app.config.get('plugin_manager')
    plugins = {}
    
    if plugin_manager:
        plugins = plugin_manager.get_plugins()
        
    return render_template('chains/edit.html', chain={}, plugins=plugins, action_title="Nowy", action_url="/chains/save")

@chains_bp.route('/chains/edit/<chain_id>', methods=['GET'])
def edit_chain(chain_id):
    """
    Wyświetla formularz do edycji istniejącego łańcucha.
    
    Args:
        chain_id (str): Identyfikator łańcucha do edycji
    """
    chains = load_chains()
    if chain_id not in chains:
        flash('Łańcuch o podanym identyfikatorze nie istnieje', 'danger')
        return redirect(url_for('chains.list_chains'))
    
    # Pobierz łańcuch
    chain = chains[chain_id]
    
    # Dodaj ID do obiektu łańcucha dla wygody formularza
    chain_data = {
        'id': chain_id,
        'description': chain.get('description', ''),
        'steps': []
    }
    
    # Przetwarzanie triggera
    trigger = chain.get('trigger', '')
    if trigger.startswith('webhook:'):
        chain_data['webhook'] = {
            'endpoint': trigger.split(':', 1)[1],
            'methods': ['POST']  # Domyślnie POST
        }
    elif trigger.startswith('mqtt:'):
        chain_data['mqtt'] = {
            'topic': trigger.split(':', 1)[1],
            'qos': 1  # Domyślnie QoS 1
        }
    
    # Przetwarzanie kroków
    for step in chain.get('steps', []):
        step_data = {
            'plugin': step.get('plugin', ''),
            'params': step.get('params', {})
        }
        chain_data['steps'].append(step_data)
    
    # Pobierz informacje o dostępnych pluginach
    plugin_manager = current_app.config.get('plugin_manager')
    plugins = {}
    
    if plugin_manager:
        plugins = plugin_manager.get_plugins()
    
    return render_template('chains/edit.html', chain=chain_data, plugins=plugins, action_title="Edytuj", 
                          action_url=f"/chains/update/{chain_id}")

@chains_bp.route('/chains/save', methods=['POST'])
def save_chain():
    """Zapisuje nowy łańcuch na podstawie danych z formularza."""
    # Sprawdź, czy przekazano surowy JSON
    if 'raw_json' in request.form and request.form['raw_json'].strip():
        try:
            chainData = json.loads(request.form['raw_json'])
        except json.JSONDecodeError:
            flash('Nieprawidłowy format JSON', 'danger')
            return redirect(url_for('chains.new_chain'))
    else:
        # Tworzenie obiektu łańcucha z danych formularza
        chainData = build_chain_from_form(request.form)
    
    # Walidacja podstawowych pól
    if not chainData.get('id'):
        flash('Identyfikator łańcucha jest wymagany', 'danger')
        return render_template('chains/edit.html', chain=chainData, action_title="Nowy", 
                              action_url="/chains/save")
    
    # Sprawdź, czy łańcuch o podanym ID już istnieje
    chains = load_chains()
    if chainData['id'] in chains:
        flash(f'Łańcuch o identyfikatorze "{chainData["id"]}" już istnieje', 'danger')
        return render_template('chains/edit.html', chain=chainData, action_title="Nowy", 
                              action_url="/chains/save")
    
    # Dodaj łańcuch do konfiguracji
    chains[chainData['id']] = {k: v for k, v in chainData.items() if k != 'id'}
    
    # Zapisz zmiany
    save_chains(chains)
    
    flash(f'Łańcuch "{chainData["id"]}" został pomyślnie utworzony', 'success')
    return redirect(url_for('chains.list_chains'))

@chains_bp.route('/chains/update/<chain_id>', methods=['POST'])
def update_chain(chain_id):
    """
    Aktualizuje istniejący łańcuch na podstawie danych z formularza.
    
    Args:
        chain_id (str): Identyfikator łańcucha do aktualizacji
    """
    # Sprawdź, czy łańcuch istnieje
    chains = load_chains()
    if chain_id not in chains:
        flash('Łańcuch o podanym identyfikatorze nie istnieje', 'danger')
        return redirect(url_for('chains.list_chains'))
    
    # Sprawdź, czy przekazano surowy JSON
    if 'raw_json' in request.form and request.form['raw_json'].strip():
        try:
            chainData = json.loads(request.form['raw_json'])
        except json.JSONDecodeError:
            flash('Nieprawidłowy format JSON', 'danger')
            return redirect(url_for('chains.edit_chain', chain_id=chain_id))
    else:
        # Tworzenie obiektu łańcucha z danych formularza
        chainData = build_chain_from_form(request.form)
    
    # Aktualizuj łańcuch
    chains[chain_id] = {k: v for k, v in chainData.items() if k != 'id'}
    
    # Zapisz zmiany
    save_chains(chains)
    
    flash(f'Łańcuch "{chain_id}" został pomyślnie zaktualizowany', 'success')
    return redirect(url_for('chains.list_chains'))

@chains_bp.route('/chains/delete/<chain_id>', methods=['POST'])
def delete_chain(chain_id):
    """
    Usuwa istniejący łańcuch.
    
    Args:
        chain_id (str): Identyfikator łańcucha do usunięcia
    """
    # Sprawdź, czy łańcuch istnieje
    chains = load_chains()
    if chain_id not in chains:
        flash('Łańcuch o podanym identyfikatorze nie istnieje', 'danger')
        return redirect(url_for('chains.list_chains'))
    
    # Usuń łańcuch
    del chains[chain_id]
    
    # Zapisz zmiany
    save_chains(chains)
    
    flash(f'Łańcuch "{chain_id}" został pomyślnie usunięty', 'success')
    return redirect(url_for('chains.list_chains'))

# API REST dla łańcuchów

@chains_bp.route('/api/chains', methods=['GET'])
def api_get_chains():
    """Zwraca listę wszystkich łańcuchów w formacie JSON."""
    chains = load_chains()
    return jsonify({"status": "success", "chains": chains})

@chains_bp.route('/api/chains/<chain_id>', methods=['GET'])
def api_get_chain(chain_id):
    """
    Zwraca konkretny łańcuch w formacie JSON.
    
    Args:
        chain_id (str): Identyfikator łańcucha
    """
    chains = load_chains()
    if chain_id not in chains:
        return jsonify({"status": "error", "message": "Łańcuch nie znaleziony"}), 404
    
    return jsonify({"status": "success", "chain": chains[chain_id]})

@chains_bp.route('/api/chains', methods=['POST'])
def api_create_chain():
    """Tworzy nowy łańcuch na podstawie danych z żądania JSON."""
    if not request.is_json:
        return jsonify({"status": "error", "message": "Oczekiwano danych w formacie JSON"}), 400
    
    chainData = request.get_json()
    
    # Sprawdź, czy podano ID łańcucha
    if 'id' not in chainData:
        return jsonify({"status": "error", "message": "Brak wymaganego pola 'id'"}), 400
    
    # Sprawdź, czy łańcuch o podanym ID już istnieje
    chains = load_chains()
    if chainData['id'] in chains:
        return jsonify({"status": "error", "message": f"Łańcuch o ID '{chainData['id']}' już istnieje"}), 409
    
    # Dodaj łańcuch do konfiguracji
    chain_id = chainData.pop('id')
    chains[chain_id] = chainData
    
    # Zapisz zmiany
    save_chains(chains)
    
    return jsonify({"status": "success", "message": "Łańcuch utworzony pomyślnie", "id": chain_id}), 201

@chains_bp.route('/api/chains/<chain_id>', methods=['PUT'])
def api_update_chain(chain_id):
    """
    Aktualizuje istniejący łańcuch na podstawie danych z żądania JSON.
    
    Args:
        chain_id (str): Identyfikator łańcucha do aktualizacji
    """
    if not request.is_json:
        return jsonify({"status": "error", "message": "Oczekiwano danych w formacie JSON"}), 400
    
    # Sprawdź, czy łańcuch istnieje
    chains = load_chains()
    if chain_id not in chains:
        return jsonify({"status": "error", "message": "Łańcuch nie znaleziony"}), 404
    
    # Aktualizuj łańcuch
    chainData = request.get_json()
    chains[chain_id] = chainData
    
    # Zapisz zmiany
    save_chains(chains)
    
    return jsonify({"status": "success", "message": "Łańcuch zaktualizowany pomyślnie"})

@chains_bp.route('/api/chains/<chain_id>', methods=['DELETE'])
def api_delete_chain(chain_id):
    """
    Usuwa istniejący łańcuch.
    
    Args:
        chain_id (str): Identyfikator łańcucha do usunięcia
    """
    # Sprawdź, czy łańcuch istnieje
    chains = load_chains()
    if chain_id not in chains:
        return jsonify({"status": "error", "message": "Łańcuch nie znaleziony"}), 404
    
    # Usuń łańcuch
    del chains[chain_id]
    
    # Zapisz zmiany
    save_chains(chains)
    
    return jsonify({"status": "success", "message": "Łańcuch usunięty pomyślnie"})

# Funkcje pomocnicze

def load_chains():
    """
    Wczytuje łańcuchy z pliku JSON.
    
    Returns:
        dict: Słownik łańcuchów przetwarzania
    """
    # Sprawdź, czy plik istnieje
    if not os.path.exists(CHAINS_FILE):
        # Utwórz pusty plik, jeśli nie istnieje
        os.makedirs(os.path.dirname(CHAINS_FILE), exist_ok=True)
        with open(CHAINS_FILE, 'w') as f:
            f.write('{}')
        return {}
    
    # Wczytaj łańcuchy z pliku
    try:
        with open(CHAINS_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # W przypadku błędów w pliku JSON, zwróć pusty słownik
        return {}

def save_chains(chains):
    """
    Zapisuje łańcuchy do pliku JSON.
    
    Args:
        chains (dict): Słownik łańcuchów przetwarzania
    """
    # Upewnij się, że katalog istnieje
    os.makedirs(os.path.dirname(CHAINS_FILE), exist_ok=True)
    
    # Zapisz łańcuchy do pliku
    with open(CHAINS_FILE, 'w') as f:
        json.dump(chains, f, indent=2)

def build_chain_from_form(form_data):
    """
    Tworzy obiekt łańcucha na podstawie danych z formularza.
    
    Args:
        form_data (ImmutableMultiDict): Dane z formularza
        
    Returns:
        dict: Obiekt łańcucha w formacie zgodnym z plikiem chains.json
    """
    # Podstawowe dane łańcucha
    chainData = {
        'id': form_data.get('chain_id'),
        'description': form_data.get('description', ''),
        'steps': []
    }
    
    # Trigger
    triggerType = form_data.get('trigger_type')
    if triggerType == 'webhook':
        endpoint = form_data.get('webhook_endpoint', '')
        chainData['trigger'] = f'webhook:{endpoint}'
    elif triggerType == 'mqtt':
        topic = form_data.get('mqtt_topic', '')
        chainData['trigger'] = f'mqtt:{topic}'
    
    # Kroki
    # Przetwarzanie kroków z formularza
    step_indices = set()
    for key in form_data:
        if key.startswith('steps[') and key.endswith('][plugin]'):
            # Wyciągnij indeks z nazwy pola, np. 'steps[0][plugin]' -> '0'
            index = key[key.find('[')+1:key.find(']')]
            step_indices.add(index)
    
    # Budowanie kroków w odpowiedniej kolejności
    for index in sorted(step_indices, key=int):
        # Pobierz nazwę pluginu
        plugin_name = form_data.get(f'steps[{index}][plugin]', '')
        
        # Sprawdź, czy to jest zdalny plugin niestandardowy
        if plugin_name == 'remote:':
            # Pobierz pełną nazwę zdalnego pluginu z dodatkowego pola
            remote_plugin_name = form_data.get(f'remote_plugin_name_{index}', '')
            if remote_plugin_name:
                plugin_name = remote_plugin_name
        
        # Parametry pluginu w formacie JSON
        params_json = form_data.get(f'steps[{index}][params]', '{}')
        try:
            params = json.loads(params_json)
        except json.JSONDecodeError:
            params = {}
        
        # Tworzenie kroku w formacie zgodnym z chains.json
        step = {
            'plugin': plugin_name
        }
        
        # Dodaj parametry, jeśli istnieją i nie są pustym obiektem
        if params and params != {}:
            step['params'] = params
        
        chainData['steps'].append(step)
    
    return chainData

from flask import Blueprint, request, jsonify, current_app
import logging

# Konfiguracja loggera
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Utworzenie blueprintu dla webhooków
webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/hook/<modul>', methods=['POST'])
def handle_webhook(modul):
    """
    Obsługa webhooków pod adresem /hook/<modul>
    
    Args:
        modul (str): Nazwa modułu, do którego kierowany jest webhook
        
    Returns:
        Response: Odpowiedź JSON z informacją o statusie przetwarzania
    """
    # Sprawdzenie czy dane przychodzące są w formacie JSON
    if not request.is_json:
        logger.warning(f"Otrzymano nieprawidłowe dane (nie JSON) dla modułu {modul}")
        return jsonify({"status": "error", "message": "Oczekiwano danych w formacie JSON"}), 400
    
    # Pobranie danych JSON
    daneJson = request.get_json()
    
    # Logowanie otrzymanych danych
    logger.info(f"Webhook dla modułu '{modul}' otrzymał dane: {daneJson}")
    
    # Utworzenie triggera dla Chain Engine
    triggerId = f"webhook:{modul}"
    
    # Próba uruchomienia odpowiedniego chaina
    try:
        # Dostęp do Chain Engine z kontekstu aplikacji
        chainEngine = current_app.config.get('chain_engine')
        
        if chainEngine:
            # Sprawdzenie, czy istnieje chain dla tego triggera
            chainId, chain = chainEngine.get_chain_for_trigger(triggerId)
            
            if chainId:
                logger.info(f"Znaleziono chain '{chainId}' dla triggera '{triggerId}'. Uruchamianie...")
                
                # Uruchomienie chaina
                result = chainEngine.run_chain(triggerId, daneJson)
                
                return jsonify({
                    "status": "success", 
                    "message": f"Dane dla modułu {modul} zostały przetworzone przez chain {chainId}",
                    "result": result
                })
            else:
                logger.info(f"Nie znaleziono chaina dla triggera '{triggerId}'. Dane zostały tylko zalogowane.")
        else:
            logger.warning("Chain Engine nie jest dostępny w kontekście aplikacji")
    
    except Exception as e:
        logger.error(f"Błąd podczas przetwarzania danych przez Chain Engine: {e}")
    
    # Jeśli nie znaleziono chaina lub wystąpił błąd, zwracamy standardową odpowiedź
    return jsonify({"status": "success", "message": f"Dane dla modułu {modul} zostały przyjęte"})

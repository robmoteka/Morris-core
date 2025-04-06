"""
Punkt wejścia do aplikacji Morris Core
Umożliwia uruchomienie aplikacji za pomocą komendy: python -m morris
"""
import os
import sys
import argparse
import logging
from morris import create_app

# Konfiguracja loggera
logger = logging.getLogger(__name__)

def main():
    """
    Główna funkcja uruchamiająca aplikację
    """
    # Parsowanie argumentów wiersza poleceń
    parser = argparse.ArgumentParser(description='Morris Core - System automatyzacji')
    parser.add_argument('--config', '-c', default='dev',
                        choices=['dev', 'prod', 'test'],
                        help='Konfiguracja środowiska (dev, prod, test)')
    parser.add_argument('--host', default='0.0.0.0',
                        help='Host na którym uruchomić aplikację')
    parser.add_argument('--port', '-p', type=int, default=5000,
                        help='Port na którym uruchomić aplikację')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Uruchom w trybie debug')
    
    args = parser.parse_args()
    
    # Tworzenie aplikacji z odpowiednią konfiguracją
    app = create_app(args.config)
    
    # Zapisanie PID do pliku
    with open('morris.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    # Uruchomienie aplikacji
    logger.info(f"Uruchamianie Morris Core v{app.config['VERSION']} na {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()

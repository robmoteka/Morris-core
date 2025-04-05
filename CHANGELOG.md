# Change Log

## [0.0.3] - 2025-04-05

### Added

- Wertykalne zakładki dla kroków w edytorze łańcuchów
- Lepsze wsparcie dla zdalnych pluginów niestandardowych
- Domyślne opcje pluginów przy tworzeniu nowego łańcucha

### Fixed

- Naprawiono problem z pustą listą pluginów przy tworzeniu nowego kroku
- Poprawiono obsługę zdarzeń w zakładkach Bootstrap
- Naprawiono błędy parsowania JSON w parametrach pluginów
- Ulepszono obsługę pól formularza dla zdalnych pluginów
- Poprawiono wyświetlanie opisu pluginu po wyborze z listy

## [0.0.2] - 2025-04-05

### Fixed

- Rozwiązano problem z podświetlaniem składni w edytorze JavaScript w pliku [templates/chains/edit.html](cci:7://file:///home/robert/PROJEKTY/Morris-core/templates/chains/edit.html:0:0-0:0)
- Usunięto zagnieżdżony kod Jinja2 z JavaScript
- Przeniesiono dane z szablonu Jinja2 do osobnego elementu script typu application/json
- Usunięto niepotrzebne bloki {% raw %} i {% endraw %}
- Poprawiono błąd składni w znaczniku script dla JSONEditor

## [0.0.1] - 2025-04-05

### Added

- Podstawowa architektura aplikacji
- Silnik chainów (chain_engine.py)
- System pluginów
- Komunikacja MQTT
- REST API
- Obsługa webhooków

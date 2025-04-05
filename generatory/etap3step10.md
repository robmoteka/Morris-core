Masz przed sobą kod odpowiedzialny za obsługę lokalnych wtyczek w systemie Morris – modularnej, rozproszonej aplikacji przetwarzającej dane przez łańcuchy (chainy) zbudowane z wtyczek (plugins).

Zweryfikuj, czy implementacja lokalnych wtyczek (`BasePlugin`) działa zgodnie z założeniami projektu.

🔍 Sprawdź następujące aspekty:

1. Czy istnieje klasa bazowa `BasePlugin`, zawierająca co najmniej metodę:

   - `process(input_data: dict, config: dict) -> dict`
   - Czy klasy dziedziczące mogą łatwo ją rozszerzyć?

2. Czy lokalne wtyczki są umieszczone w katalogu (np. `plugins/`) i ładowane dynamicznie lub ręcznie rejestrowane przez `PluginManager`?

3. Czy przykładowe wtyczki zostały zaimplementowane i spełniają interfejs:

   - `LoggerPlugin` – loguje dane
   - `UppercasePlugin` – zamienia teksty na wielkie litery
   - Inne testowe

4. Czy Chain Engine potrafi używać lokalnych wtyczek jako kroków w chainie?

   - Czy dane są przekazywane do metody `process(...)` i wynik trafia do kolejnego kroku?

5. Czy lokalna wtyczka może być dodana do chaina przez UI i działa po uruchomieniu webhooka lub triggera MQTT?

📂 Uwzględnij strukturę plików:

- `plugins/base.py` – klasa bazowa
- `plugins/logger_plugin.py`, `plugins/uppercase_plugin.py` – przykłady
- `plugin_manager.py`, `chain_engine.py` – integracja

📑 Odnieś się do dokumentu `Opis Modulu Core.md`, sekcja:

- **3. Wtyczki (Plugins)**
- **4. Chainy (Przepływy)**

🧪 Na końcu:

- Oceń, czy implementacja spełnia wymagania projektu
- Zgłoś braki, błędy lub niezgodności
- Zaproponuj testy jednostkowe dla wtyczek i integracyjne z chain engine

Uznaj komponent za gotowy, jeśli lokalne wtyczki są:

- zgodne z interfejsem,
- dają się rejestrować i wywoływać,
- są dostępne przez chain engine.

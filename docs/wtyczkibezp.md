Bezpieczeństwo wymiany danych między Core a wtyczkami zewnętrznymi
✅ Założenia
Każda zewnętrzna wtyczka (remote plugin) musi posiadać własny panel administracyjny dostępny tylko po logowaniu.

Wtyczki i Core będą komunikować się przez MQTT lub REST z wykorzystaniem klucza API (shared secret).

Klucz API będzie:

wyświetlany i zarządzany w panelu Core

dostępny również w panelu administracyjnym wtyczki (np. do rejestracji lub synchronizacji)

Wtyczki będą musiały się zarejestrować/uwierzytelnić podczas uruchamiania.

📑 Szczegóły
🔑 Wymiana klucza:
Core generuje unikalny klucz API dla każdej zewnętrznej wtyczki (przy pierwszym połączeniu lub ręcznie).

Wtyczka loguje się do swojego panelu (/admin) z danymi:

Login: robert@moteka.pl

Hasło: Morrisprzyniesmi4owocemang0 (może być zmienione)

Wtyczka przechowuje klucz lokalnie i dołącza go do:

nagłówków HTTP (Authorization: Bearer <token>)

wiadomości MQTT (pole auth_token)

🔐 Obsługa w Core:
Core weryfikuje token (JWT, HMAC, lub static token z bazy)

Odrzuca niezaufane/zmanipulowane komunikaty

Pozwala na rotację klucza

🧑‍💻 Panel administracyjny wtyczki:
Login ekran (autoryzacja lokalna lub przez Core)

Sekcja: „Parametry połączenia z Core”

Adres Core

Klucz API (ręczne wklejenie lub automatyczna synchronizacja)

Sekcja: „Parametry działania pluginu” (indywidualne per plugin)

Masz przed sobą kod panelu administracyjnego systemu Morris – modularnej aplikacji zarządzającej chainami i wtyczkami.  
Zweryfikuj, czy implementacja frontendu i powiązanego backendu działa zgodnie z dokumentem „Opis Modułu Core.md”, który znajduje się w katalogu głównym projektu.

🔍 Sprawdź następujące funkcje:

1. Czy istnieje trasa `GET /chains`, która renderuje listę zdefiniowanych chainów?

   - Czy w tabeli widnieją: nazwa, trigger, liczba kroków?
   - Czy przy każdym chainie są przyciski „Edytuj”, „Usuń”?

2. Czy działa trasa `GET /chains/edit/<chain_id>`?

   - Czy formularz zawiera pola: nazwa, trigger (dropdown), lista kroków (plugin + JSON konfig)?
   - Czy możliwe jest dodawanie/usuwanie kroków przez JavaScript?

3. Czy formularz chaina zapisuje dane przez `POST /chains/save`?

   - Czy zapis trafia do `chains.json` lub odpowiedniego storage?
   - Czy dane są walidowane?

4. Czy `/plugins` pokazuje aktualną listę zarejestrowanych wtyczek?

   - Czy tabela zawiera: nazwa, typ, opis, status?
   - Czy pluginy zgłoszone przez MQTT są widoczne?

5. Czy możliwe jest ręczne dodanie pluginu (`POST /plugins`)?

6. Czy UI korzysta z Bootstrap 5 i Jinja2?
   - Czy jest responsywny i czytelny?
   - Czy pola formularzy są opatrzone etykietami?

📦 **Pliki do uwzględnienia**:

- `templates/chains/list.html`
- `templates/chains/edit.html`
- `templates/plugins/list.html`
- `static/js/form_chains.js`
- `routes/chains.py`, `routes/plugins.py`
- `plugins.json`, `chains.json`

📁 **Uwaga**:
Dokument projektowy znajduje się w `Opis Modulu Core.md`. Zweryfikuj zgodność z jego sekcjami:

- „Panel webowy”
- „Chainy (Przepływy)”
- „Wtyczki (Plugins)”

⚠️ Jeśli coś nie działa lub jest niezgodne z opisem, wskaż:

- co należy poprawić,
- które pliki trzeba zmienić,
- jakie testy (manualne lub jednostkowe) można dodać.

Na końcu oceń, czy komponent można uznać za ukończony i przejść do kolejnego etapu roadmapy.

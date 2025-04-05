# 📍 Roadmap – Asystent Morris

## ✅ Etap 1: Fundament – Moduł główny (Core)

- ✅ Krok 1: Wybór technologii (Flask, MQTT, REST, WebHooki)
- ✅ Krok 2: Opis architektury i wymagań (`Opis Modulu Core.md`)
- ✅ Krok 3: Szkielet aplikacji Flask + webhook + MQTT client
- ✅ Krok 4: Chain Engine – uruchamianie chainów po triggerze
- ✅ Krok 5: Plugin Manager – rejestracja, statusy, metadane

---

## ✅ Etap 2: Webowy panel (Admin UI)

- ✅ Krok 6: Widok i edycja chainów (Jinja2, Bootstrap, JS)
- ✅ Krok 7: Widok i zarządzanie wtyczkami (status, opis, dodawanie)
- ✅ Krok 8: Obsługa zapisu danych do JSON / API
- ✅ Krok 9: Walidacja poprawności z dokumentem `Opis Modulu Core.md`

---

## 🧪 Etap 3: Obsługa wtyczek

- ✅ Krok 10: Lokalne wtyczki (`BasePlugin`, np. `LoggerPlugin`, `UppercasePlugin`)
- [ ] Krok 11: Zdalne wtyczki przez MQTT/REST (pełna obsługa input/output)
- [ ] Krok 12: Testowe chainy przetwarzające dane (np. demo z webhookiem)

---

## 🔌 Etap 4: Konektory (Bridges)

- ✅ Krok 13: Bridge WhatsApp (webhook + MQTT)
- [ ] Krok 14: Bridge Smart Home (lokalny MQTT)
- [ ] Krok 15: Publikowanie `plugin/announce` przez bridge

---

## ⏱️ Etap 5: Chain Engine – rozszerzenia

- [ ] Krok 16: Obsługa warunków w chainach (`if/else`)
- [ ] Krok 17: Retry, timeouty, obsługa błędów
- [ ] Krok 18: Rejestrowanie wyników, logi przetwarzania

---

## 🧭 Etap 6: Actions (nowość)

- [ ] Krok 19: Mechanizm „Actions” – zadeklarowane akcje uruchamiające chainy z parametrami
- [ ] Krok 20: Harmonogramy czasowe (cykliczne, jednorazowe)
- [ ] Krok 21: UI do zarządzania akcjami (formularz, lista, logika)

---

📄 Dokument główny: `Opis Modulu Core.md`  
📝 Status: Ostatni zakończony krok: **Etap 2, Krok 9**

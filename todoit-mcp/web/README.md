# TODOIT Web Interface

Responsywna aplikacja webowa do zarządzania listami TODO z wykorzystaniem FastAPI i Tabulator.js.

## 🎯 Funkcjonalności

### ✅ Zaimplementowane
- **Responsywny design** - działa na desktop i mobile
- **Tabulator.js** - zaawansowana tabela z sortowaniem, filtrowaniem
- **Nested tables** - subitemy wyświetlane jako zagnieżdżone tabele
- **Edycja inline** - bezpośrednia edycja treści i statusów
- **Konfiguracja kolumn** - pokazywanie/ukrywanie kolumn
- **Ulubione listy** - gwiazdka przy ulubionych listach
- **Wyszukiwanie** - filtrowanie po nazwie listy, kluczu itemu, treści
- **Filtry statusów** - filtrowanie po statusach zadań
- **Toast notyfikacje** - informacje o sukcesie/błędach

### 🔄 Planowane ulepszenia
- Bulk operations (masowe operacje)
- Drag & drop dla pozycji
- Dark mode
- Export/Import
- Statystyki i wykresy

## 🚀 Szybki start

### 1. Instalacja zależności

```bash
cd todoit-mcp
pip install fastapi uvicorn jinja2
```

### 2. Uruchomienie aplikacji

```bash
cd web
uvicorn app:app --reload --port 8000
```

### 3. Dostęp do aplikacji

Otwórz przeglądarkę i idź do:
```
http://localhost:8000
```

## 🏗️ Architektura

```
web/
├── app.py                 # FastAPI backend
├── static/
│   ├── css/
│   │   └── style.css      # Responsywny CSS
│   └── js/
│       └── app.js         # Logika Tabulator
├── templates/
│   └── index.html         # Single-page aplikacja
└── README.md              # Ta dokumentacja
```

## 📱 Responsywność

### Desktop (> 768px)
- Wszystkie kolumny widoczne
- Nested tables w pełni rozwinięte
- Pełny interfejs konfiguracji

### Tablet (768px - 480px)
- Automatyczne ukrywanie mniej ważnych kolumn
- Kompaktowy interfejs
- Zachowana pełna funkcjonalność

### Mobile (< 480px)
- Minimal UI - najważniejsze kolumny
- Touch-friendly buttons
- Skrócone nested tables

## 🔧 API Endpoints

### Lists & Items
```
GET  /api/lists                              # Wszystkie listy z itemami
GET  /api/lists/{list_key}/items             # Itemy konkretnej listy
PUT  /api/items/{list_key}/{item_key}        # Aktualizuj item
PUT  /api/subitems/{list_key}/{item_key}/{subitem_key}  # Aktualizuj subitem
POST /api/lists/{list_key}/favorite          # Toggle ulubione
```

### Configuration
```
GET  /api/config                             # Pobierz konfigurację
POST /api/config                             # Zapisz konfigurację
```

### Health Check
```
GET  /api/health                             # Status aplikacji
```

## 🎨 Konfiguracja kolumn

Dostępne kolumny:
- ⭐ **Ulubione** - gwiazdka
- **Lista** - nazwa listy
- **Item** - klucz itemu
- **Treść** - zawartość zadania
- **Status** - status zadania
- **Pozycja** - kolejność w liście
- **Utworzono** - data utworzenia
- **Zaktualizowano** - data modyfikacji

Konfiguracja jest zapisywana w localStorage przeglądarki.

## 🔍 Wyszukiwanie i filtry

### Wyszukiwanie globalne
Przeszukuje:
- Nazwę listy
- Klucz itemu  
- Treść zadania

### Filtry
- **Status** - dropdown z dostępnymi statusami
- **Ulubione** - pokazuje tylko ulubione listy
- **Sortowanie** - kliknięcie nagłówka kolumny

## 📱 Nested Tables (Subitemy)

### Funkcjonalność
- Automatyczne wyświetlanie subitemów jako zagnieżdżone tabele
- Edycja inline bezpośrednio w subtabeli
- Kolorowanie statusów także w subtabelach
- Responsywne ukrywanie na mobile

### Interakcja
- **Double-click** na wierszu głównym - pokazuje/ukrywa subitemy
- **Edycja inline** - kliknij w komórkę subitemu
- **Status colors** - kolorowe linie po lewej stronie

## 🎯 Statusy zadań

| Status | Kolor | Znaczenie |
|--------|-------|-----------|
| `pending` | Szary | Oczekujące |
| `in_progress` | Niebieski | W trakcie |
| `completed` | Zielony | Ukończone |
| `failed` | Czerwony | Nieudane |

## 🔧 Konfiguracja środowiska

### Zmienne środowiskowe
```bash
export TODOIT_DB_PATH=/tmp/test_todoit.db  # Ścieżka do bazy danych
```

### Rozwój (development)
```bash
# Auto-reload podczas zmian
uvicorn app:app --reload --port 8000

# Debug mode
TODOIT_DEBUG=1 uvicorn app:app --reload --port 8000
```

### Produkcja
```bash
# Standardowy serwer
uvicorn app:app --host 0.0.0.0 --port 8000

# Z wieloma workerami
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🐛 Troubleshooting

### Baza danych nie działa
```bash
# Sprawdź ścieżkę
echo $TODOIT_DB_PATH

# Upewnij się że katalog istnieje
mkdir -p $(dirname $TODOIT_DB_PATH)
```

### Port zajęty
```bash
# Znajdź proces na porcie 8000
lsof -i :8000

# Użyj innego portu
uvicorn app:app --port 8001
```

### Problemy z Tabulator
- Sprawdź console developera (F12)
- Upewnij się że CDN Tabulator jest dostępny
- Sprawdź błędy JavaScript w konsoli

## 📊 Performance Tips

### Dla dużej ilości danych
- Zwiększ `itemsPerPage` w konfiguracji
- Użyj filtrów do ograniczenia wyświetlanych danych
- Rozważ pagination na poziomie API

### Mobile optimization
- Aplikacja automatycznie ukrywa kolumny na mobile
- Nested tables są kompaktowe na małych ekranach
- Touch-friendly interface

## 🤝 Contributing

1. Fork repository
2. Utwórz feature branch
3. Commit zmiany
4. Push do branch
5. Otwórz Pull Request

## 📄 Licencja

MIT License - zobacz plik LICENSE w głównym katalogu projektu.
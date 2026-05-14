# ytrans

CLI-утилита для извлечения транскрипций YouTube-видео. Сохраняет в заданную папку как `.md`.

## Установка

```bash
# Зависимости
pip3 install youtube-transcript-api
brew install yt-dlp  # нужен для каналов

# Алиас в ~/.zshrc
ytrans() {
  YTRANS_DIR="$HOME/<your_folder_with_documents>" \
  python3 <your_folder_with_this_project>/transcript.py "$@"
}
```

## Использование

### Одно видео

```bash
ytrans "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Плейлист

```bash
# Автоопределение по list= в URL
ytrans "https://www.youtube.com/playlist?list=PLrAXtmErZgOe..."

# Или явно с -p
ytrans -p "https://www.youtube.com/watch?v=xxx&list=PLrAXt..."
```

### Канал — топ популярных видео

```bash
# Топ 10 (по умолчанию)
ytrans "https://www.youtube.com/@channelname"

# Топ 5
ytrans -n 5 "https://www.youtube.com/@channelname"
```

### Флаги

| Флаг | Описание |
|------|----------|
| `--lang ru,en` | Приоритет языков субтитров (по умолчанию: `ru,en`) |
| `--timestamps` | Добавить `[MM:SS]` перед каждой строкой |
| `-o path` | Сохранить в конкретный файл |
| `-p` | Принудительно обработать как плейлист |
| `-n N` | Количество топ видео с канала (по умолчанию: 10) |

### Примеры

```bash
# С таймкодами
ytrans --timestamps "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Только английские субтитры
ytrans --lang en "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# В stdout (без YTRANS_DIR)
python3 transcript.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" > transcript.txt
```

## Как это работает

- Видео/плейлист: `youtube-transcript-api` (Python)
- Каналы (топ видео): `yt-dlp` для получения списка, затем `youtube-transcript-api` для транскрипции
- Файлы сохраняются как `{video_id}.md` с заголовком `# Название видео`
- Уже скачанные видео пропускаются (проверка по файлу)

## Ограничения

- Приватные видео — нет доступа
- Age-restricted — не поддерживается (ограничение библиотеки)
- Видео без субтитров — пропускаются
- При массовом скачивании YouTube может временно заблокировать IP (429). Решение: VPN или подождать

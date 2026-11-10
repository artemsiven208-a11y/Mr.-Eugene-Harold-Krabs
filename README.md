# Telegram-бот для конвертации файлов

Бот принимает файл в Telegram, показывает подходящие форматы и отправляет результат обратно. Пользователю достаточно отправить файл и нажать нужную кнопку.

## Что умеет бот

- принимает документы, изображения, таблицы, аудио и видео;
- определяет формат по имени, MIME-типу и содержимому;
- показывает только реально доступные направления;
- ищет формат по тексту и понимает простые опечатки;
- хранит каждый файл во временной папке и удаляет её после работы;
- ограничивает размер файла, время конвертации и число тяжёлых задач;
- оставляет исходный файл доступным для повторной конвертации.

## Какие форматы поддерживаются

| Исходный файл | Результат | Чем выполняется |
|---|---|---|
| PNG, JPG/JPEG, WEBP, BMP, TIFF, GIF | другие изображения, PDF | Pillow |
| PDF | TXT, PNG, JPG | PyMuPDF |
| TXT | PDF, HTML | Python, PyMuPDF |
| MD | HTML, PDF | Python, PyMuPDF |
| DOCX | PDF, TXT, HTML | python-docx, PyMuPDF |
| RTF | TXT, PDF | Python, PyMuPDF |
| CSV | XLSX | openpyxl |
| XLSX | CSV | openpyxl |
| DOC, ODT, XLS, ODS, PPT, PPTX, ODP | офисные форматы и PDF | LibreOffice |
| MP3, WAV, OGG, FLAC, M4A | другие аудиоформаты | FFmpeg |
| MP4, WEBM, MOV, MKV | другие видеоформаты, MP3 | FFmpeg |

LibreOffice и FFmpeg подключаются автоматически. Если программа не найдена, связанные кнопки скрываются. DOCX → PDF всё равно доступен: без LibreOffice сохраняются текст и таблицы, но сложное оформление упрощается.

## Установка и запуск на Windows

В PowerShell из корня проекта:

~~~powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
winget install --id TheDocumentFoundation.LibreOffice --accept-source-agreements --accept-package-agreements
winget install --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
Copy-Item .env.example .env
notepad .env
python main.py
~~~

В файле .env укажите токен:

~~~env
BOT_TOKEN=токен_от_BotFather
MAX_FILE_SIZE_MB=20
MAX_CONCURRENT_JOBS=3
TEMP_FILE_TTL_MINUTES=30
CONVERSION_TIMEOUT_SECONDS=120
~~~

После установки LibreOffice и FFmpeg перезапустите PowerShell. Бот также проверяет стандартный путь LibreOffice: C:\Program Files\LibreOffice\program\soffice.exe.

## Установка на Linux

~~~bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
sudo apt update
sudo apt install -y libreoffice ffmpeg
cp .env.example .env
python main.py
~~~

## Как пользоваться

1. Отправьте или перешлите файл боту.
2. Выберите формат кнопкой.
3. Получите готовый файл. Для нового результата используйте кнопки под тем же сообщением.

Если нужного формата нет в списке, нажмите «Другой формат» и напишите, например, pdf, .jpg, ворд или эксель.

## Команды

- /start — открыть главное меню;
- /help — краткая подсказка;
- /formats — показать направления, доступные на этом компьютере;
- /cancel — отменить текущий выбор и удалить временные файлы.

## Где находится код

~~~text
main.py                 запуск бота и регистрация команд
bot/                    Telegram-сообщения, кнопки и состояния пользователя
converters/             обработчики форматов и общий реестр конвертаций
utils/config.py         настройки из .env
utils/file_detection.py определение исходного формата
utils/file_manager.py   временные папки, имена и очистка
tests/                  локальные тесты
~~~

Главное место для добавления нового направления — converters/registry.py: там регистрируется источник, результат и функция обработки. Саму обработку следует держать в отдельном файле converters/, а не добавлять большие условия в main.py.

## Ограничения

- максимальный размер задаётся MAX_FILE_SIZE_MB;
- PDF-сканы не распознаются: OCR в проекте нет;
- PDF → DOCX может потерять исходную структуру;
- GIF при преобразовании в неподвижное изображение сохраняет первый кадр;
- сложное оформление офисных документов лучше сохраняется через LibreOffice;
- HTML читается как документ и не исполняется.

## Проверка

~~~powershell
pytest -q
python -m compileall -q .
~~~

Тесты проверяют определение форматов, поиск с опечаткой, очистку временных папок, TXT → PDF, PDF → TXT, PNG → JPG, JPG → WEBP, DOCX → PDF и CSV/XLSX. Проверка реального Telegram-чата требует запущенного бота и настоящего токена.

@echo off
REM Setup Script for Local Development (Windows)
REM Этот скрипт автоматически поднимает всё необходимое для разработки

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   Super Market Fintech - Local Development Setup          ║
echo ║   Автоматическое поднятие окружения (Windows)             ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM ============================================================================
REM ПРОВЕРКА ТРЕБОВАНИЙ
REM ============================================================================

echo [STEP] 1. Проверка требований...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python не найден! Установите https://www.python.org
    pause
    exit /b 1
)
echo [OK] Python найден

docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Docker найден
    set USE_DOCKER=true
) else (
    echo [WARNING] Docker не найден. Используйте локальную установку PostgreSQL/Redis
    set USE_DOCKER=false
)

echo.

REM ============================================================================
REM СОЗДАНИЕ ВИРТУАЛЬНОГО ОКРУЖЕНИЯ
REM ============================================================================

echo [STEP] 2. Настройка виртуального окружения...

if not exist ".venv" (
    echo [STEP] Создание виртуального окружения...
    python -m venv .venv
    echo [OK] Виртуальное окружение создано
) else (
    echo [OK] Виртуальное окружение уже существует
)

REM Активировать виртуальное окружение
call .venv\Scripts\activate.bat
echo [OK] Виртуальное окружение активировано
echo.

REM ============================================================================
REM УСТАНОВКА ЗАВИСИМОСТЕЙ
REM ============================================================================

echo [STEP] 3. Установка зависимостей...

if not exist "requirements.txt" (
    echo [ERROR] requirements.txt не найден!
    pause
    exit /b 1
)

echo [STEP] Установка зависимостей из requirements.txt...
python -m pip install --upgrade pip setuptools wheel >nul 2>&1
pip install -r requirements.txt

echo [OK] Зависимости установлены
echo.

REM ============================================================================
REM ПОДНЯТЬ DOCKER КОНТЕЙНЕРЫ (опционально)
REM ============================================================================

if "%USE_DOCKER%"=="true" (
    echo [STEP] 4. Поднятие Docker контейнеров...

    REM PostgreSQL
    docker ps --format "{{.Names}}" 2>nul | findstr /x "super_market_db" >nul
    if %errorlevel% equ 0 (
        echo [WARNING] Контейнер super_market_db уже запущен
    ) else (
        echo [STEP] Запуск PostgreSQL контейнера...
        docker run -d ^
            --name super_market_db ^
            -e POSTGRES_DB=super_market ^
            -e POSTGRES_USER=postgres ^
            -e POSTGRES_PASSWORD=postgres ^
            -p 5432:5432 ^
            postgres:14
        timeout /t 3 /nobreak >nul
        echo [OK] PostgreSQL контейнер запущен
    )

    REM Redis
    docker ps --format "{{.Names}}" 2>nul | findstr /x "super_market_redis" >nul
    if %errorlevel% equ 0 (
        echo [WARNING] Контейнер super_market_redis уже запущен
    ) else (
        echo [STEP] Запуск Redis контейнера...
        docker run -d ^
            --name super_market_redis ^
            -p 6379:6379 ^
            redis:7
        echo [OK] Redis контейнер запущен
    )

    echo.
) else (
    echo [STEP] 4. Проверка локального PostgreSQL/Redis...

    REM Проверить PostgreSQL
    psql -U postgres -h localhost -c "SELECT 1" >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] PostgreSQL доступен локально
    ) else (
        echo [ERROR] PostgreSQL не доступен! Запустите его вручную
        pause
        exit /b 1
    )

    REM Проверить Redis
    redis-cli ping >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Redis доступен локально
    ) else (
        echo [WARNING] Redis не доступен. Может не потребоваться для базовых тестов
    )

    echo.
)

REM ============================================================================
REM СОЗДАТЬ/ПРОВЕРИТЬ .env FILE
REM ============================================================================

echo [STEP] 5. Проверка .env файла...

if not exist ".env" (
    if exist ".env.example" (
        echo [STEP] Создание .env из .env.example...
        copy .env.example .env >nul
        echo [OK] .env создан

        echo.
        echo [WARNING] ВАЖНО: Отредактируйте .env и добавьте реальные ключи:
        echo   - BOT_TOKEN (от BotFather: https://t.me/BotFather^)
        echo   - LOLZTEAM_API_KEY (от https://api.lolzteam.net^)
        echo   - PRIMARY_ENCRYPTION_KEY (сгенерирован или скопирован^)
        echo.
        echo Команда для генерации Fernet ключа:
        echo   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode(^))"
        echo.
        pause
    ) else (
        echo [ERROR] .env.example не найден!
        pause
        exit /b 1
    )
) else (
    echo [OK] .env уже существует
)

echo.

REM ============================================================================
REM ВЫПОЛНИТЬ МИГРАЦИИ БД
REM ============================================================================

echo [STEP] 6. Выполнение миграций БД...

python manage.py migrate --check >nul 2>&1
if %errorlevel% equ 0 (
    echo [WARNING] БД уже миграирована
) else (
    echo [STEP] Запуск миграций...
    python manage.py migrate
    echo [OK] Миграции выполнены
)

echo.

REM ============================================================================
REM ЗАГРУЗИТЬ ТЕСТОВЫЕ ДАННЫЕ
REM ============================================================================

echo [STEP] 7. Загрузка тестовых данных...

python manage.py shell << PYTHON_END
from apps.market.models import Category, Product

if Category.objects.count() > 0:
    print("OK Категории уже загружены")
else:
    print("STEP Создание категорий...")

    cat_electronics = Category.objects.create(
        name="Электроника",
        description="Электронные устройства"
    )

    cat_books = Category.objects.create(
        name="Книги",
        description="Книги и литература"
    )

    print("OK Категории созданы")

if Product.objects.count() > 0:
    print("OK Товары уже загружены")
else:
    print("STEP Создание товаров...")

    cat_electronics = Category.objects.first()

    if cat_electronics:
        Product.objects.create(
            name="iPhone 14 Pro",
            price=99990,
            description="Флагманский смартфон Apple",
            category=cat_electronics
        )

        Product.objects.create(
            name="Samsung Galaxy S24",
            price=79990,
            description="Смартфон Samsung",
            category=cat_electronics
        )

    print("OK Товары созданы")
PYTHON_END

echo [OK] Тестовые данные загружены
echo.

REM ============================================================================
REM ЗАПУСТИТЬ ТЕСТЫ
REM ============================================================================

echo [STEP] 8. Запуск тестов...
echo.

echo [STEP] Запуск Stage 3 Bot тестов...
pytest tests/test_stage3_bot.py::TestKeyboards -v --tb=short

echo.

REM ============================================================================
REM ИТОГОВАЯ ИНФОРМАЦИЯ
REM ============================================================================

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   OK ОКРУЖЕНИЕ ГОТОВО К РАЗРАБОТКЕ!                        ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo Полезные команды:
echo   - Запустить тесты:
echo     pytest tests/ -v
echo.
echo   - Запустить Django сервер:
echo     python manage.py runserver
echo.
echo   - Открыть Django shell:
echo     python manage.py shell
echo.
echo   - Посмотреть статус Docker:
echo     docker ps
echo.
echo   - Остановить Docker контейнеры:
echo     docker stop super_market_db super_market_redis
echo.
echo   - Удалить Docker контейнеры:
echo     docker rm super_market_db super_market_redis
echo.

echo Документация:
echo   - DEVELOPMENT.md - Локальная разработка
echo   - QUICK_START_KEYS.md - Управление ключами
echo   - TROUBLESHOOTING_SETUP.md - Решение проблем
echo   - docs/KEYS_AND_SECRETS.md - Полная информация
echo.

echo OK Setup завершён успешно!
pause

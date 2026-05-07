#!/bin/bash

# Setup Script for Local Development
# Этот скрипт автоматически поднимает всё необходимое для разработки

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Super Market Fintech - Local Development Setup          ║"
echo "║   Автоматическое поднятие окружения                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# ФУНКЦИИ
# ============================================================================

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

check_command() {
    if command -v $1 &> /dev/null; then
        print_success "$1 найден"
        return 0
    else
        print_error "$1 не найден"
        return 1
    fi
}

# ============================================================================
# ПРОВЕРКА ТРЕБОВАНИЙ
# ============================================================================

print_step "1. Проверка требований..."

if ! check_command "python"; then
    print_error "Python не установлен! Установите https://www.python.org"
    exit 1
fi

if ! check_command "docker"; then
    print_warning "Docker не установлен. Используйте локальную установку PostgreSQL/Redis"
    USE_DOCKER=false
else
    USE_DOCKER=true
    print_success "Docker установлен"
fi

echo ""

# ============================================================================
# СОЗДАНИЕ ВИРТУАЛЬНОГО ОКРУЖЕНИЯ
# ============================================================================

print_step "2. Настройка виртуального окружения..."

if [ ! -d ".venv" ]; then
    print_step "Создание виртуального окружения..."
    python -m venv .venv
    print_success "Виртуальное окружение создано"
else
    print_success "Виртуальное окружение уже существует"
fi

# Активировать виртуальное окружение
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    # Windows
    source .venv/Scripts/activate
fi

print_success "Виртуальное окружение активировано"
echo ""

# ============================================================================
# УСТАНОВКА ЗАВИСИМОСТЕЙ
# ============================================================================

print_step "3. Установка зависимостей..."

if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt не найден!"
    exit 1
fi

pip install --upgrade pip setuptools wheel > /dev/null
print_step "Установка зависимостей из requirements.txt..."
pip install -r requirements.txt > /dev/null

print_success "Зависимости установлены"
echo ""

# ============================================================================
# ПОДНЯТЬ DOCKER КОНТЕЙНЕРЫ (опционально)
# ============================================================================

if [ "$USE_DOCKER" = true ]; then
    print_step "4. Поднятие Docker контейнеров..."

    # PostgreSQL
    if docker ps --format '{{.Names}}' | grep -q "super_market_db"; then
        print_warning "Контейнер super_market_db уже запущен"
    else
        print_step "Запуск PostgreSQL контейнера..."
        docker run -d \
            --name super_market_db \
            -e POSTGRES_DB=super_market \
            -e POSTGRES_USER=postgres \
            -e POSTGRES_PASSWORD=postgres \
            -p 5432:5432 \
            postgres:14 > /dev/null
        sleep 3  # Дождать инициализации
        print_success "PostgreSQL контейнер запущен"
    fi

    # Redis
    if docker ps --format '{{.Names}}' | grep -q "super_market_redis"; then
        print_warning "Контейнер super_market_redis уже запущен"
    else
        print_step "Запуск Redis контейнера..."
        docker run -d \
            --name super_market_redis \
            -p 6379:6379 \
            redis:7 > /dev/null
        print_success "Redis контейнер запущен"
    fi

    # Проверить подключение
    sleep 1
    print_step "Проверка подключений..."

    if docker exec super_market_db pg_isready -U postgres > /dev/null; then
        print_success "PostgreSQL доступен"
    else
        print_error "PostgreSQL не доступен"
        exit 1
    fi

    if redis-cli ping > /dev/null 2>&1; then
        print_success "Redis доступен"
    else
        print_error "Redis не доступен"
        exit 1
    fi

    echo ""
else
    print_step "4. Проверка локального PostgreSQL/Redis..."

    if psql -U postgres -h localhost -c "SELECT 1" > /dev/null 2>&1; then
        print_success "PostgreSQL доступен локально"
    else
        print_error "PostgreSQL не доступен! Запустите его вручную"
        exit 1
    fi

    if redis-cli ping > /dev/null 2>&1; then
        print_success "Redis доступен локально"
    else
        print_warning "Redis не доступен. Может не потребоваться для базовых тестов"
    fi

    echo ""
fi

# ============================================================================
# СОЗДАТЬ/ПРОВЕРИТЬ .env FILE
# ============================================================================

print_step "5. Проверка .env файла..."

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        print_step "Создание .env из .env.example..."
        cp .env.example .env
        print_success ".env создан"

        print_warning "ВАЖНО: Отредактируйте .env и добавьте реальные ключи:"
        echo "  - BOT_TOKEN (от BotFather: https://t.me/BotFather)"
        echo "  - LOLZTEAM_API_KEY (от https://api.lolzteam.net)"
        echo "  - PRIMARY_ENCRYPTION_KEY (сгенерирован или скопирован)"
        echo ""
        echo "Команда для генерации Fernet ключа:"
        echo "  python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        echo ""
    else
        print_error ".env.example не найден!"
        exit 1
    fi
else
    print_success ".env уже существует"
fi

echo ""

# ============================================================================
# ВЫПОЛНИТЬ МИГРАЦИИ БД
# ============================================================================

print_step "6. Выполнение миграций БД..."

if python manage.py migrate --check > /dev/null 2>&1; then
    print_warning "БД уже миграирована"
else
    print_step "Запуск миграций..."
    python manage.py migrate
    print_success "Миграции выполнены"
fi

echo ""

# ============================================================================
# ЗАГРУЗИТЬ ТЕСТОВЫЕ ДАННЫЕ
# ============================================================================

print_step "7. Загрузка тестовых данных..."

python manage.py shell << EOF
from apps.market.models import Category, Product

# Проверить есть ли уже данные
if Category.objects.count() > 0:
    print("✅ Категории уже загружены")
else:
    print("📥 Создание категорий...")

    cat_electronics = Category.objects.create(
        name="Электроника",
        description="Электронные устройства"
    )

    cat_books = Category.objects.create(
        name="Книги",
        description="Книги и литература"
    )

    print("✅ Категории созданы")

# Проверить товары
if Product.objects.count() > 0:
    print("✅ Товары уже загружены")
else:
    print("📥 Создание товаров...")

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

    print("✅ Товары созданы")
EOF

print_success "Тестовые данные загружены"
echo ""

# ============================================================================
# ЗАПУСТИТЬ ТЕСТЫ
# ============================================================================

print_step "8. Запуск тестов..."
echo ""

print_step "Запуск Stage 3 Bot тестов..."
pytest tests/test_stage3_bot.py::TestKeyboards -v --tb=short

echo ""

# ============================================================================
# ИТОГОВАЯ ИНФОРМАЦИЯ
# ============================================================================

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   ✅ ОКРУЖЕНИЕ ГОТОВО К РАЗРАБОТКЕ!                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "Полезные команды:"
echo "  🧪 Запустить тесты:"
echo "     pytest tests/ -v"
echo ""
echo "  🌐 Запустить Django сервер:"
echo "     python manage.py runserver"
echo ""
echo "  🐚 Открыть Django shell:"
echo "     python manage.py shell"
echo ""
echo "  📊 Посмотреть статус Docker:"
echo "     docker ps"
echo ""
echo "  ⏹️  Остановить Docker контейнеры:"
echo "     docker stop super_market_db super_market_redis"
echo ""
echo "  🧹 Удалить Docker контейнеры:"
echo "     docker rm super_market_db super_market_redis"
echo ""

echo "📚 Документация:"
echo "  - DEVELOPMENT.md - Локальная разработка"
echo "  - QUICK_START_KEYS.md - Управление ключами"
echo "  - TROUBLESHOOTING_SETUP.md - Решение проблем"
echo "  - docs/KEYS_AND_SECRETS.md - Полная информация"
echo ""

echo "✅ Setup завершён успешно!"

# Location Catalog & Analytics API

REST API для каталогу локацій із системою відгуків, динамічним підрахунком рейтингу та аналітикою переглядів.

## Стек технологій

- Python 3.12 / Django 5.1 / DRF
- PostgreSQL 16
- Redis 7
- Pandas
- Docker Compose

## Основний функціонал

- **Автентифікація:** Сесійна авторизація Django з роботою через cookies (`sessionid`, `csrftoken`), реєстрація та скидання пароля через email-токени.
- **Динамічні метрики:** Підрахунок рейтингу, кількості відгуків та популярності виконується в базі даних через ORM (`Subquery`, `Avg`, `Count`) без збереження розрахункових колонок у таблиці.
- **Трекінг переглядів:** Фіксація переглядів з лімітом 1 раз на годину для IP або користувача за допомогою атомарних операцій у Redis.
- **Кешування:** Кешування відповідей каталогу в Redis з інвалідацією через сигнали при зміні локацій чи відгуків.
- **Відгуки:** Валідація оцінки (1-5), обмеження одного відгуку на локацію від користувача, облік реакцій.
- **Експорт:** Вивантаження списків у форматах CSV та JSON.

## Запуск проєкту

1. Підготовка змінних оточення:
```bash
cp .env.example .env
```

2. Запуск через Docker Compose:
```bash
docker compose up -d
docker compose exec web python manage.py migrate
```

Сервіс доступний за адресою: `http://localhost:8001`.
Документація Swagger UI: `http://localhost:8001/api/schema/swagger-ui/`.

## Тестування

```bash
docker compose exec web pytest
```

## Ендпоінти

- `GET /api/schema/swagger-ui/` — Swagger UI
- `GET /api/auth/csrf/` — отримання CSRF токена
- `POST /api/auth/register/` — реєстрація
- `POST /api/auth/login/` — вхід
- `POST /api/auth/logout/` — вихід
- `GET /api/auth/me/` — профіль користувача
- `GET, POST /api/categories/` — категорії
- `GET, POST /api/locations/` — каталог локацій
- `GET, PUT, DELETE /api/locations/{id}/` — деталі, оновлення, видалення локації
- `GET /api/locations/export/csv/` — експорт локацій у CSV
- `GET /api/locations/export/json/` — експорт локацій у JSON
- `GET, POST /api/reviews/` — відгуки
- `GET, PUT, DELETE /api/reviews/{id}/` — деталі, оновлення, видалення відгуку
- `POST, DELETE /api/reviews/{id}/react/` — реакція на відгук (лайк / дизлайк)

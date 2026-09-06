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
- **Відгуки та сповіщення:** Валідація оцінки (1-5), обмеження одного відгуку на локацію від користувача, облік реакцій (лайк / дизлайк). Автоматичні email-сповіщення автору локації та підписникам при створенні нового відгуку.
- **Підписки:** Можливість підписатися / відписатися від оновлень локації для отримання email-повідомлень.
- **Фільтрація та пошук:** Пошук за назвою та описом, фільтрація за категорією (`category`, `category_slug`), автором (`author`, `author_username`), рейтингом (`min_rating`, `max_rating`, `rating`), сортування за датою, рейтингом та популярністю, пагінація з підтримкою `page_size`.
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
- `POST /api/auth/password-reset/` — запит на скидання пароля через email
- `POST /api/auth/password-reset-confirm/` — підтвердження скидання пароля
- `GET, POST /api/categories/` — категорії
- `GET, POST /api/locations/` — каталог локацій (фільтри: `category`, `author`, `min_rating`, `max_rating`, `ordering`, `page_size`)
- `GET, PUT, DELETE /api/locations/{id}/` — деталі, оновлення, видалення локації
- `POST, DELETE /api/locations/{id}/subscribe/` — підписка / відписка на сповіщення про нові відгуки
- `GET /api/locations/export/csv/` — експорт локацій у CSV
- `GET /api/locations/export/json/` — експорт локацій у JSON
- `GET, POST /api/reviews/` — відгуки
- `GET, PUT, DELETE /api/reviews/{id}/` — деталі, оновлення, видалення відгуку
- `POST, DELETE /api/reviews/{id}/react/` — реакція на відгук (лайк / дизлайк)

# Карта интеграции: вёрстка lost_found/site ↔ Flask-бэкенд

## Исходное состояние бэкенда (app.py, db.py)

Маршруты (до интеграции):

| Маршрут | Методы | Доступ | Шаблон | Данные |
|---|---|---|---|---|
| `/` (home) | GET | все | index.html | items (status=active): id, type, title, description, date, photo, status, category_name, place_name |
| `/register` | GET, POST | гость (вошедшего редиректит) | register.html | читает form: name, email, password, contact |
| `/login` | GET, POST | гость | login.html | читает form: email, password; query: next |
| `/logout` | POST | вошедший | — | redirect home |
| `/add` | GET, POST | @login_required | add.html | GET: categories, places; POST: category_id, place_id, type, title, description, date |
| `/item/<int:item_id>` | GET | все | item_detail.html | item (+author_name, author_contact) |
| `/dashboard` | GET | @login_required | dashboard.html | active, closed (свои items) |
| `/item/<int:item_id>/close` | POST | @login_required + только автор | — | redirect dashboard |

Таблицы: users(id,name,email,password_hash,contact), categories(id,name), places(id,name),
place_neighbors(place_id,neighbor_id), items(id,user_id,category_id,place_id,type,title,description,date,photo,status,created_at), matches(id,lost_item_id,found_item_id,score,status).
CSRFProtect не включён — скрытое поле csrf_token не нужно.

## Соответствие страниц

| Страница вёрстки | Маршрут Flask | Шаблон Jinja2 | Данные | Формы/состояния |
|---|---|---|---|---|
| index.html (главная, гость) + home-after-login.html (вошедший) | `/` | index.html | items (лента активных), current_user | Герой и features из вёрстки; под ними добавлен блок ленты объявлений (карточки item-card из lost.html, данные из БД, пустое состояние «Пока нет объявлений»). Шапка: гость — Войти/Регистрация; вошедший — имя, кабинет, Выйти (POST) |
| lost.html | `/items?type=lost` (новый маршрут items_list) | items.html | items по type=lost, categories, q, category_id | Поиск GET (q), чипы-категории как ссылки (category_id), пустое состояние |
| found.html | `/items?type=found` | items.html | то же с type=found | То же; кнопка «Сообщить о находке» |
| contact.html | `/item/<int:item_id>` | item_detail.html | item (фото, название, место, дата, описание, статус, автор) | Карточка вещи; карточка «Контактные данные»: вошедшим — имя/email/контакт автора (readonly, без кнопок «Скопировать» — они требуют JS), гостю — «Войдите, чтобы увидеть контакты автора»; автору активного объявления — POST-кнопка «Закрыть объявление» |
| login.html | `/login` | login.html | current_user, flash | POST: email, password, remember (см. изменения бэкенда); удалены: Google-кнопка, «Забыли пароль?» (нет бэкенда) |
| signup.html | `/register` | register.html | current_user, flash | POST: name, email, password, password2, terms, contact (поле contact добавлено — бэкенд читает его обязательно); удалена Google-кнопка |
| submit.html | `/add` (GET/POST, @login_required) | add.html | categories, places, current_user | POST: type (радио-переключатель вместо JS-кнопок), category_id (select из БД вместо текстового поля), place_id (select из БД вместо текстового), title, description, date (type=date); «Отмена» — ссылка на главную |
| profile.html | `/dashboard` | dashboard.html | active, closed, счётчики (total_items, found_items, matches), current_user | Аватар с инициалами, статистика из БД; строки-объявления активные и закрытые; удалены ссылки «Уведомления»/«Настройки» (нет бэкенда) |
| claim.html («Это моя вещь», заявка на возврат) | — | не реализовано | — | В бэкенде нет маршрута заявок на возврат. Блок «Контакты нашедшего» из claim.html используется на item_detail как блок контактов автора |
| notifications.html | — | не реализовано | — | Нет модели уведомлений в бэкенде; ссылки скрыты |
| settings.html | — | не реализовано | — | Нет маршрута редактирования профиля; ссылки скрыты |
| (в вёрстке нет) | 404 / 500 | 404.html, 500.html | — | Простые страницы в стиле дизайна через errorhandler |

## Состояния

- Гость: шапка с «Войти»/«Регистрация»; на /add и /dashboard — редирект на /login (Flask-Login); контакты автора скрыты.
- Вошедший: шапка с именем, иконкой профиля (→ /dashboard), кнопкой «Выйти» (POST-форма).
- Пустые состояния: лента/списки/кабинет без объявлений — текстовые заглушки без фейковых данных.
- Ошибки форм: flash-сообщения (danger/success/warning/info) — алерты, добавленные в стиле дизайна (класс alert alert--danger и т.д.).
- Бейджи: lost → «Потерял» (badge--orange), found → «Нашёл» (badge--green); статус: активный → badge--green «Активно», закрытый → badge--orange «Закрыто».

## Расхождения фронтенд ↔ бэкенд

Не хватает в бэкенде (реализовано минимально):
1. Маршруты `/items?type=lost|found` со списками — добавлены (поиск q и фильтр category_id через GET-параметры, параметризованный SQL).
2. Выдача фото `/uploads/<filename>` — добавлена через send_from_directory (в БД поле items.photo есть, сейчас во всех записях NULL → показывается заглушка-плейсхолдер из вёрстки).
3. Фильтр дат для шаблонов `ru_date` (формат 15.01.2024 из вёрстки) — добавлен.
4. Подтверждение пароля password2 на регистрации — проверка добавлена в register (несколько строк, безопасно).
5. «Запомнить меня» на входе — передаётся в login_user(remember=...).
6. Счётчики статистики профиля (Объявления/Найдено/Совпадения) — вычисляются в dashboard по БД (включая таблицу matches).
7. Обработчики 404/500.
8. Flash-алерты и пара мелких вспомогательных стилей дописаны в static/css/style.css (помечены комментарием «дополнение для интеграции»), т.к. Jinja-версии страниц серверные.

Лишнее в вёрстке (удалено/отключено):
1. Весь JavaScript (js/main.js, теги <script>): глаз пароля, чипы, переключатель типа, «Прочитать все», кнопки «Скопировать», клиентская валидация — интерактив перенесён в HTML/CSS/сервер, где возможно.
2. Google OAuth-кнопки (вход/регистрация) — нет бэкенда.
3. «Забыли пароль?», «Конфиденциальность», «Условия использования» (href="#") — нет страниц; ссылки убраны.
4. Уведомления, Настройки, Заявка на возврат — нет бэкенда; страницы не созданы, ссылки скрыты.
5. Текстовые поле «Место» на submit.html заменено select'ом place_id (бэкенд хранит place_id из справочника).
6. Кнопка «Подтвердите право на вещь» на claim.html — нет маршрута; страница не реализована.
7. Поле «Контактные данные» на submit.html — readonly с контактом из профиля (бэкенд не читает это поле; контакт берётся из users).

Логотип: папка reference/ в корне отсутствует; используется lost_found/references/logo_lost_found.png (388×368) → static/images/logo.png. В вёрстке есть свой assets/logo.svg (плоская версия того же знака); по правилу приоритет отдан файлу из reference/. favicon — тот же логотип.

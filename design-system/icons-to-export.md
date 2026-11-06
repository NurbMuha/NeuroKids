# Иконки Lordicon для экспорта (кабинет ученика, v1)

Что сделать на lordicon.com:

1. Найти каждую иконку по ключевому слову (EN). Название иконки в каталоге может немного отличаться.
2. Посмотреть, есть ли у неё значок **PRO**. Иконки без значка бесплатные, с ними нужна ссылка «Animated icons by Lordicon.com» в футере.
3. Скачать два формата:
   - **SVG** — нужен для Figma, это статичный кадр;
   - **Lottie JSON** — нужен для кода.
4. Назвать файлы по колонке «Компонент», например `system-search.svg` и `system-search.json`.
5. Положить файлы в папку `NeuroKids/design-system/icons/`. Я превращу их в компоненты Figma.

Стили:

- **System:** Outline для интерфейса, Solid для активного пункта навигации. В System можно менять только цвет.
- **Doodle:** стиль Color.

Сколько иконок бесплатно в каждом семействе, сайт показывает только в браузере. Если нужных бесплатных не окажется, переходим на PRO: $8/мес при оплате за год.

## System — интерфейс (16 / 20 / 24 / 32px)

| # | Компонент | Где используется | Поиск (EN) | Триггер |
|---|---|---|---|---|
| 1 | system-today | Таб «Сегодня» | home, sun | hover |
| 2 | system-courses | Курсы | book, education | hover |
| 3 | system-tasks | Задания | checklist, clipboard | hover |
| 4 | system-progress | Прогресс | chart, trending up | hover |
| 5 | system-achievements | Достижения | trophy, medal | hover |
| 6 | system-leaderboard | Рейтинг | podium, ranking | hover |
| 7 | system-schedule | Расписание | calendar | hover |
| 8 | system-profile | Профиль | user, avatar | hover |
| 9 | system-settings | Настройки | settings, gear | hover |
| 10 | system-search | Поиск | search | hover |
| 11 | system-bell | Уведомления | bell, notification | hover/loop* |
| 12 | system-streak | Стрик | fire, flame | in |
| 13 | system-xp | XP, очки | lightning, zap | in |
| 14 | system-menu | Меню (мобильный) | menu → close (morph) | click |
| 15 | system-close | Закрыть | close, cross | hover |
| 16 | system-logout | Выход | logout, exit | hover |
| 17 | system-plus | Добавить | plus, add | hover |
| 18 | system-edit | Редактировать | edit, pencil | hover |
| 19 | system-trash | Удалить | trash, delete | hover |
| 20 | system-download | Скачать | download | hover |
| 21 | system-upload | Загрузить | upload | hover |
| 22 | system-share | Поделиться | share | hover |
| 23 | system-link | Ссылка | link | hover |
| 24 | system-copy | Копировать | copy | click |
| 25 | system-filter | Фильтр | filter | hover |
| 26 | system-sort | Сортировка | sort, arrows | click |
| 27 | system-refresh | Обновить | refresh, reload | click |
| 28 | system-more | Ещё (⋯) | more, dots | hover |
| 29 | system-chevron-left | Назад | chevron left | hover |
| 30 | system-chevron-right | Вперёд | chevron right | hover |
| 31 | system-chevron-down | Раскрыть | chevron down | click |
| 32 | system-chevron-up | Свернуть | chevron up | click |
| 33 | system-arrow-left | Назад (крупно) | arrow left | hover |
| 34 | system-arrow-right | Далее | arrow right | hover |
| 35 | system-external | Внешняя ссылка | external link | hover |
| 36 | system-play | Воспроизвести | play → pause (morph) | click |
| 37 | system-pause | Пауза | pause | click |
| 38 | system-volume | Звук | volume, speaker | click |
| 39 | system-fullscreen | Полный экран | expand, fullscreen | hover |
| 40 | system-captions | Субтитры | subtitles, captions | click |
| 41 | system-check | Готово / верно | check, checkmark | in |
| 42 | system-info | Информация | info | hover |
| 43 | system-warning | Предупреждение | warning, alert | in |
| 44 | system-error | Ошибка | error, x circle | in |
| 45 | system-help | Помощь | help, question | hover |
| 46 | system-lock | Закрыто | lock → unlock (morph) | in |
| 47 | system-eye | Показать пароль | eye | click |
| 48 | system-eye-off | Скрыть пароль | eye off | click |
| 49 | system-clock | Время, длительность | clock | hover |
| 50 | system-timer | Таймер теста | timer, stopwatch | loop* |
| 51 | system-hint | Подсказка | lightbulb, idea | hover |
| 52 | system-star | Избранное, оценка | star | click |
| 53 | system-heart | Нравится | heart | click |
| 54 | system-bookmark | Закладка | bookmark | click |
| 55 | system-chat | Помощник / чат | chat, message | hover |
| 56 | system-mic | Голосовой ответ | microphone | click |
| 57 | system-attach | Прикрепить файл | attachment, paperclip | hover |
| 58 | system-language | Язык RU/KZ/EN | globe, language | hover |
| 59 | system-calendar-check | Дедлайн выполнен | calendar check | in |
| 60 | system-grid | Вид «плиткой» | grid, layout | click |

\* `loop` при `prefers-reduced-motion` заменяется статичным кадром.

## Doodle (Color) — состояния (48 / 64 / 96px)

| # | Компонент | Где используется | Поиск (EN) | Триггер |
|---|---|---|---|---|
| 1 | doodle-empty-tasks | Нет заданий | empty, checklist done | in |
| 2 | doodle-empty-courses | Нет курсов | books, library | in |
| 3 | doodle-empty-search | Ничего не найдено | search, magnifier | in |
| 4 | doodle-lesson-done | Урок пройден | success, confetti | in |
| 5 | doodle-achievement | Новое достижение | trophy, medal | in → loop* |
| 6 | doodle-streak | Стрик продлён | fire | in |
| 7 | doodle-level-up | Новый уровень | rocket | in |
| 8 | doodle-star | Награда / XP | star | in |
| 9 | doodle-error | Что-то пошло не так | error, bug | in |
| 10 | doodle-offline | Нет сети | wifi off, cloud off | in |
| 11 | doodle-locked | Контент закрыт | lock | in |
| 12 | doodle-welcome | Онбординг | hand wave, hello | in |
| 13 | doodle-idea | Подсказка / мысль | lightbulb, idea | in |
| 14 | doodle-time-up | Время вышло | hourglass, alarm | in |
| 15 | doodle-calendar | Пустое расписание | calendar | in |
| 16 | doodle-bell | Нет уведомлений | bell | in |
| 17 | doodle-brain | Бренд «Neuro», мысль | brain | in |
| 18 | doodle-target | Цель недели | target | in |
| 19 | doodle-gift | Подарок / бонус | gift | in |
| 20 | doodle-like | Отзыв / «нравится» | like, thumbs up | in |

Цвета Doodle Color: в редакторе Lordicon подставьте цвета палитры NeuroKids, чтобы иконки не выбивались из системы:

- синий `#0061EF`;
- шафран `#FFCE00`;
- розовый `#FFA1CC`;
- аква `#00A4FF`;
- зелёный `#02873E`;
- ультрафиолет `#3B197F`;
- графит `#2D2C2B` для контура.

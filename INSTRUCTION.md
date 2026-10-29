# Инструкция: запуск AI-агента ApplyPilot и подготовка данных

Этот документ описывает, как с нуля настроить агента, который сам находит вакансии и откликается на них,
и как подготовить личные данные, чтобы отклики были персонализированы под вас.

Рабочий проект: корень репозитория (Next.js дашборд **JobSync** + Python-движок **autopilot**).
Код автопилота — в `tools/autopilot.py`, конфиг — в `autopilot/`. Все команды ниже выполняются из корня репозитория.

---

## 1. Установка

> **macOS/Linux:** используйте `python3` и `pip3` (команд `python`/`pip` там обычно нет).
> Рекомендуемый способ — виртуальное окружение:
> ```sh
> python3 -m venv .venv && source .venv/bin/activate   # после этого можно писать просто python/pip
> ```
> Если активировать venv не хотите, во всех командах ниже заменяйте `python3` на `python`.

```sh
# 1) Python-зависимости ядра агента
pip3 install -r requirements.txt
pip3 install -r requirements-dev.txt      # для тестов (опционально)

# 2) Браузер для автоматизации форм
python3 -m playwright install chromium    # пропустите, если у вас установлен Google Chrome
                                         # (browser.channel = "chrome" по умолчанию)

# 3) Опционально: OCR для сканированных PDF резюме
#    Установите Tesseract: https://github.com/tesseract-ocr/tesseract

# 4) Дашборд JobSync (Next.js) — опционально, агент работает и без него
npm install
```

Проверка окружения:

```sh
python3 tools/autopilot.py doctor         # проверяет config.json, CV, LLM-цепочку, почту
```

---

## 2. Конфигурация и секреты

### 2.1 Создать конфиг

```sh
cp autopilot/config.example.json autopilot/config.json
```

(создастся автоматически при первом запуске, но лучше сразу отредактировать).

### 2.2 Секреты — только в файле секретов, НЕ в config.json

```sh
mkdir -p ~/.config/search-work-world
cp autopilot/secrets.env.example ~/.config/search-work-world/secrets.env
chmod 600 ~/.config/search-work-world/secrets.env
# альтернатива: export AUTOPILOT_SECRETS_FILE=/ваш/путь/secrets.env
```

Заполните нужные ключи (все опциональны — используйте только то, что включено):

| Переменная | Для чего |
|---|---|
| `OPENAI_API_KEY`, `AUTOPILOT_LLM_BASE_URL` | LLM через OpenAI-совместимый API |
| `LLM7_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `TOKENHARBOR_API_KEY` | альтернативные LLM-провайдеры |
| `AUTOPILOT_EMAIL_ADDRESS`, `AUTOPILOT_EMAIL_APP_PASSWORD` | чтение писем с исходами заявок (Gmail — только app password!) |
| `ADZUNA_APP_ID/KEY`, `JOOBLE_API_KEY`, `TAVILY_API_KEY` | дополнительные источники вакансий |

CLI-провайеры (`claude`, `codex`, `grok`, `opencode`) работают без ключей — используют уже установленный CLI.

### 2.3 Включить LLM-провайдер

Все провайдеры в `config.json` выключены по умолчанию. Включите один из них:

```sh
python3 tools/autopilot.py llm --probe              # проверить доступность всех
python3 tools/autopilot.py llm --enable groq        # включить провайдера из списка providers
python3 tools/autopilot.py llm --set-model <name> <model>
```

LLM нужен для ответов на нестандартные вопросы анкет; ответы строятся строго на тексте вашего CV
(защита от выдумки), кэшируются и при отсутствии LLM попадают в `qa --pending` — то есть ждут вашего ответа.

---

## 3. Подготовка данных (персонализация под вас)

Это самый важный раздел. Всё, что делает отклики «вашими», живёт в `autopilot/config.json`.

### 3.1 Профиль (`profile`) — автозаполнение форм

Заполните своими данными вместо Jane Doe:

```jsonc
"profile": {
  "first_name": "Ваше имя",
  "last_name": "Фамилия",
  "full_name": "Имя Фамилия",          // должен СОВПАДАТЬ с именем на CV — проверка агента!
  "email": "you@example.com",
  "phone": "+49 ...",                   // формат с кодом страны
  "phone_country_code": "49",           // только цифры, без +
  "location": "Berlin, Germany",
  "country": "Germany",
  "languages": "English, Russian, German",
  "linkedin": "https://linkedin.com/in/...",
  "github": "https://github.com/...",
  "work_authorization": "...",          // ваше разрешение на работу (если есть)
  "notice_period": "1 month",
  "salary_expectation": "60,000 - 80,000 EUR",
  "school": "...", "degree": "...", "discipline": "...",
  "years_experience": "3",
  "portfolio": "..."                    // ссылка на портфолио (для креативных ролей)
}
```

### 3.2 Резюме и персоны — главный инструмент персонализации

Одна персона = одна профессия = одно CV. Загрузите **своё** CV:

```sh
mkdir -p autopilot/resumes
cp ~/моё_резюме.pdf autopilot/resumes/appsec.pdf       # CV кладём сюда (папка в gitignore)

python3 tools/autopilot.py resume add \
  --file autopilot/resumes/appsec.pdf \
  --role "Application Security Engineer"               # или ваша роль
```

Что делает `resume add`:
- создаёт/обновляет персону в `personas.<key>` с путём к CV;
- **сам генерирует поисковые термины по вашему CV**: `keywords`, `required_title_terms`,
  `good_terms`, `bad_terms`, `excluded_title_terms` (niche_terms) — больше не нужно руками
  переписывать захардкоженные списки AppSec из примера;
- обновлённые термины полностью заменяют встроенные списки для этой персоны.

Полезно после смены CV или роли:

```sh
python3 tools/autopilot.py resume list                  # посмотреть персоны
python3 tools/autopilot.py resume add --regen           # перегенерировать термины заново
python3 tools/autopilot.py resume remove <key>
```

Требования к CV:
- PDF (сканы поддерживаются через OCR, если установлен Tesseract);
- имя на CV должно совпадать с `profile.full_name`;
- держите отдельный файл на каждую персону (`appsec.pdf`, `creative.pdf`, ...).

Для второй профессии:

```sh
python3 tools/autopilot.py resume add --file autopilot/resumes/creative.pdf \
  --name creative --role "Photographer / Videographer"
```

### 3.3 Bio для сопроводительного письма

Впишите себя в `personas.<key>.profile.bio` — текст используется в fallback cover letter, когда
LLM недоступен. Также можно задать `persona.profile.school/degree/discipline`, если они отличаются
от основного профиля. Персона может переопределять `name` и `email` профиля (например, разные адреса
для разных площадок).

### 3.4 Ответы на типовые вопросы (`apply.answers`)

Ключевые поля анкет. Пустая строка = «спроси меня» (вопрос уйдёт в `qa --pending` и на дашборд).
Обязательно заполните как минимум:

```jsonc
"apply": { "answers": {
  "visa": "...",                       // нужна ли спонсорская виза
  "work_authorization": "...",
  "why": "Почему вы/эта компания — ваш честный ответ одной фразой",
  "open_to_relocation": "Yes",        // или ваш личный ответ; пусто = спрашивать
  "open_to_onsite": "...",
  ...
}}
```

`apply.require_sponsorship`:
- `true` — вам нужна визовая поддержка; агент сам отсеет вакансии «no sponsorship»
  (список фраз в `search.no_relocation_terms`);
- `false` — не нужна (тогда пункты про релокацию в дефолтных good/bad terms можно почистить);
- `null` — неизвестно: вопросы про визу оставляются вам.

### 3.5 Поиск: где искать (`jobspy`, `vendor_boards`, `search`)

- `jobspy.locations` — оставьте только ваши рынки (по умолчанию список из ~16 городов мира);
- `jobspy.sites` — indeed / google / linkedin (LinkedIn: только posting'и с собственных досок компаний, Easy Apply не трогается);
- `vendor_boards` — добавьте карьерные API-доски компаний, которые вам интересны
  (форматы Greenhouse/Lever/Ashby/SmartRecruiters/Workable видны в примерах);
- `search.blocked_companies` — чёрный список компаний;
- `hours_old` — свежесть вакансий (по умолчанию 336 ч = 14 дней).

Если термины поиска после `resume add` всё же кажутся нерелевантными — правьте `personas.<key>.search` вручную
или запускайте аналитику:

```sh
python3 tools/autopilot.py keywords                     # какие ключевые слова реально дают вакансии
python3 tools/autopilot.py analyze_rejections.py        # анализ причин отказов (скорректируйте bad_terms)
```

### 3.6 Тон общения и стиль (LLM-персонализация ответов)

Ответы на открытые вопросы генерируются LLM на основе CV. Чтобы стилизовать их под себя:
- заполните `bio` (см. 3.3) — он попадает в контекст;
- задайте свои формулировки в `apply.answers.why` и других ключах — правила и кэш (`qa_answers`)
  предпочитают ваши текстовые варианты, а не выдуманные LLM;
- проверяйте подозрительные кэшированные ответы: `python3 tools/autopilot.py qa --audit`,
 Pending правите через `qa --label/--key/--set`.

---

## 4. Первый запуск — безопасный маршрут

Начинайте строго по этой цепочке, от консервативного к автономному:

```sh
# 0) Диагностика
python3 tools/autopilot.py doctor

# 1) Только сбор вакансий (без откликов)
python3 tools/autopilot.py discover --source vendor --max-keywords 5

# 2) Посмотреть очередь: что агент собирается отправлять
python3 tools/autopilot.py queue
python3 tools/autopilot.py status

# 3) Dry run: заполнить форму, НИЧЕГО не отправляя
python3 tools/autopilot.py apply --dry-run --max 1

# 4) Ассистированный режим: видимый браузер, агент заполняет, прикладывает CV и cover letter,
#    решает CAPTCHA и жмёт Submit ВЫ (до manual_wait_seconds)
python3 tools/autopilot.py apply --review --submit --max 5

# 5) Полностью автономно — только когда доверяете результатам --review
python3 tools/autopilot.py apply --submit

# Полный цикл: discover + apply
python3 tools/autopilot.py run --dry-run
python3 tools/autopilot.py run --review --max 5
```

Отклик по конкретной ссылке:

```sh
python3 tools/autopilot.py apply-url <url> --review
```

Логика порога качества: `apply.min_score_to_apply` и `personas.<key>.min_cv_match`
(минимум совпадений ключевых слов CV↔вакансия, по умолчанию 15) — вакансии ниже порога не отправляются.

---

## 5. Обратная связь и ведение

```sh
python3 tools/autopilot.py inbox --apply     # прочитать письма-исходы и обновить статусы
python3 tools/autopilot.py followups         # просроченные отклики без ответа
python3 tools/autopilot.py outreach          # пакеты для писем рекрутерам (--export-csv)
python3 tools/autopilot.py ghost             # найти компании-«призраки» (вечно висят вакансии)
python3 tools/autopilot.py block --from-ghost --apply   # занести их в blocked_companies
python3 tools/autopilot.py ats <job>         # разбор разрыва CV vs текст вакансии
python3 tools/autopilot.py qa --pending      # вопросы, требующие вашего ответа
python3 tools/autopilot.py manual            # формы, ожидающие вашего клика
python3 tools/autopilot.py outcome <job> --status Interview   # вручную пометить исход
python3 tools/autopilot.py clean             # почистить старые скриншоты
```

Вход в площадки один раз (сессия сохранится в `autopilot/browser-state.json` — не коммитить!):

```sh
python3 tools/autopilot.py login https://www.linkedin.com/login
```

---

## 6. Чек-лист персонализации (коротко)

- [ ] `profile.*` — все поля реальными данными; `full_name` == имя на CV
- [ ] Своё CV лежит в `autopilot/resumes/<persona>.pdf`
- [ ] Выполнено `resume add` → термины поиска перегенерированы под ваш CV
- [ ] `personas.<key>.profile.bio` написана вами (для cover letters)
- [ ] `apply.require_sponsorship` выставлен верно (true/false, не null)
- [ ] `apply.answers` — заполнены visa / why / relocation / onsite
- [ ] `jobspy.locations` и `vendor_boards` — только ваши рынки и компании
- [ ] Включён хотя бы один LLM-провайдер (`llm --enable ...`) или готовы разбирать `qa --pending`
- [ ] Первые прогоны — только `--dry-run` и `--review`
- [ ] `.env`, `secrets.env`, `jobs.db`, `browser-state.json`, `resumes/` не попали в git (всё в gitignore)

## 7. Частые проблемы

| Симптом | Причина / решение |
|---|---|
| `doctor` ругается на CV | имя на PDF не совпадает с `profile.full_name`; пересоберите CV или профиль |
| Вопросы анкет остаются пустыми | нет активного LLM-провайдера → `llm --probe`, затем `llm --enable`; либо заполните `apply.answers` |
| Слишком много нерелевантных вакансий | термины ещё из примера — выполните `resume add --regen`; проверьте `keywords` |
| Агент не отправляет ничего | dry_run=true по умолчанию; порог `min_cv_match`; `queue` покажет причины фильтрации |
| CAPTCHA / логин площадки | решите в окне `--review`; для постоянных сессий — `login <url>` |

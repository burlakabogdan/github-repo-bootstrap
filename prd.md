
# ТЗ: Skill для IDE — GitHub Repo Bootstrap + Commit Assistant

## 1. Мета і результат

### Мета

Створити **skill для IDE**, який:

1. **Один раз** налаштовує репозиторій на GitHub (Issues, labels, templates, Projects v2 user-level).
2. Під час розробки **перед комітом / під час PR** допомагає заповнювати необхідні поля і підтримувати дисципліну процесу (посилання на issue, тип роботи, пріоритет, статус у Project тощо).

### Результат

* Репозиторій уніфікований (шаблони issue/PR, лейбли, Project v2, мінімальні правила).
* Розробник не забуває:

  * прив’язати коміт/PR до issue,
  * вибрати тип і пріоритет,
  * оновити статус у Project,
  * заповнити мінімальні метадані в PR.

---

## 2. Контекст і обмеження

* GitHub Projects v2 керуються через **GraphQL API**.
* Репозиторні речі (labels, файли `.github/*`, settings) — через **REST API**.
* Проект **user-level** (належить акаунту, не org).
* Skill працює в 2 режимах: `solo` / `team` (різниця: CODEOWNERS/рев’ю/політики).

---

## 3. Терміни

* **Bootstrap** — одноразове налаштування репозиторію.
* **Commit Assistant** — інтерактивний помічник перед комітом / перед push / перед PR.
* **Project** — GitHub Projects v2 (user-level).
* **Issue** — одиниця роботи.
* **Item** — елемент у Project (посилання на issue/PR/draft).

---

## 4. Персона і сценарії (User Stories)

### US1: Bootstrap репозиторію

Як розробник, я хочу запустити команду “Bootstrap GitHub repo”, щоб skill створив/оновив потрібні налаштування без ручної рутини.

### US2: Створення задачі з IDE

Як розробник, я хочу створити issue з шаблону прямо з IDE і одразу додати його в Project зі статусом `Backlog`.

### US3: Робота по гілці/issue

Як розробник, я хочу створити гілку з правильним іменем на основі issue і щоб skill міг з цього автоматично визначати issue_id.

### US4: Допомога при коміті

Як розробник, я хочу щоб перед комітом skill:

* перевіряв наявність issue_id,
* підказував тип зміни,
* формував commit message,
* за потреби оновлював статус у Project (`In progress`) і пріоритет.

### US5: Підготовка PR

Як розробник, я хочу щоб при створенні PR skill:

* підставив шаблон PR,
* додав ключове слово `Fixes #ID` (за вибором),
* перевів issue/Project item у `Review`.

---

## 5. Scope

### In-scope (обов’язково)

1. **Bootstrap**

* увімкнути Issues;
* створити labels (`type:*`, `p0/p1/p2`, опційно `area:*`);
* додати файли:

  * `.github/ISSUE_TEMPLATE/task.md`
  * `.github/ISSUE_TEMPLATE/bug.md`
  * `.github/ISSUE_TEMPLATE/config.yml`
  * `.github/PULL_REQUEST_TEMPLATE.md`
  * `CODEOWNERS` (тільки team mode, опційно)
* створити/оновити **Projects v2 (user-level)**:

  * Project: `Work` (або конфігурована назва)
  * поля:

    * `Status` (Backlog, Ready, In progress, Review, Done)
    * `Priority` (P0, P1, P2)
  * views:

    * `Board` (group by Status)
    * `Backlog` (table)

2. **Commit Assistant**

* визначення issue_id з:

  * назви гілки (`feat/123-title`, `fix/123-title`) або
  * вибору issue зі списку відкритих;
* генерація commit message (конвенція + issue reference);
* перевірки перед комітом (мінімальний набір);
* синхронізація Project item статусів:

  * перший коміт по issue → `In progress`
  * PR відкритий → `Review`
  * issue закрите/merge з `Fixes #ID` → `Done`

### Out-of-scope (не робимо в v1)

* Повноцінний CI/CD, автоматичні релізи, підпис артефактів.
* Складні policy для branch protection (можливо v2).
* Автоматичне визначення “правильного” пріоритету (лише підказка/вибір).

---

## 6. Вхідні дані і конфігурація

### Конфіг-файл у репо

`/.github/repo-skill.yml` (або `.repo-skill.yml` у корені)

```yml
version: 1
github:
  owner: "USER_NAME"
  repo: "repo-name"
  default_branch: "main"

mode: "solo" # solo|team

labels:
  type: ["type:bug","type:feature","type:refactor","type:docs"]
  priority: ["p0","p1","p2"]
  area: []

projects_v2:
  enabled: true
  title: "Work"
  fields:
    status: ["Backlog","Ready","In progress","Review","Done"]
    priority: ["P0","P1","P2"]

commit_assistant:
  enforce_issue_link: true
  branch_issue_pattern: '^(feat|fix|chore|docs|refactor)/(?P<id>\d+)(-.+)?$'
  commit_format: "{type}({scope}): {subject} #{issue}"
  allowed_types: ["feat","fix","refactor","docs","chore","test"]
  default_scope: "core"
  auto_project_status:
    on_first_commit: "In progress"
    on_pr_open: "Review"
    on_issue_close: "Done"
```

---

## 7. Функціональні вимоги

### 7.1 Bootstrap: repo settings

**FR-BOOT-001**: Skill має перевірити налаштування репозиторію і увімкнути Issues (idempotent).
**FR-BOOT-002**: Skill має створити/оновити labels згідно конфігурації, без дублікатів.
**FR-BOOT-003**: Skill має створити/оновити файли шаблонів у `.github/` через Contents API (створення або update через SHA).
**FR-BOOT-004**: Якщо `mode=team` і `codeowners.enabled=true`, створити `CODEOWNERS`.

### 7.2 Bootstrap: Projects v2 (user-level)

**FR-PROJ-001**: Skill має знайти user project з назвою `Work` (або `projects_v2.title`). Якщо не знайдено — створити.
**FR-PROJ-002**: Skill має створити/оновити поля:

* `Status` (single select) з заданими опціями
* `Priority` (single select) з заданими опціями
  **FR-PROJ-003**: Skill має створити/перевірити views:
* Board (group by Status)
* Table (Backlog)
  **FR-PROJ-004**: Skill має вміти **додавати Issue в Project** як item і задавати значення полів (Status/Priority).

### 7.3 Issue creation з IDE

**FR-ISS-001**: Skill має показати форму створення issue на основі `Task` або `Bug` шаблону.
**FR-ISS-002**: Після створення issue:

* додати в Project `Work`,
* поставити `Status=Backlog`,
* (опційно) `Priority=P2` за замовчуванням.

### 7.4 Branch helper

**FR-BR-001**: Skill має створювати гілку з шаблоном:

* `feat/<issue_id>-slug`
* `fix/<issue_id>-slug`
* `docs/<issue_id>-slug`
  **FR-BR-002**: Skill має визначати `issue_id` з поточної гілки за regex з конфіга.

### 7.5 Commit Assistant (pre-commit UI)

**FR-COMMIT-001**: Перед комітом skill перевіряє:

* є `issue_id` (з гілки або з вибору issue), якщо `enforce_issue_link=true`
* commit message відповідає формату
  **FR-COMMIT-002**: Skill відкриває коротку форму:
* `type` (feat/fix/…)
* `scope`
* `subject` (коротко)
* `issue_id` (авто або вибір зі списку open issues)
  → генерує commit message.

**FR-COMMIT-003**: Перший коміт по issue:

* якщо issue ще не додано до Project → додати
* встановити `Status=In progress` (якщо увімкнено `auto_project_status.on_first_commit`)

**FR-COMMIT-004**: Якщо локально немає доступу до API (offline):

* дозволити коміт, але попередити і поставити в чергу “sync later” (локальний queue).

### 7.6 PR Assistant (optional v1, strongly recommended)

**FR-PR-001**: При створенні PR skill:

* підтягує PR template
* пропонує додати `Fixes #<issue_id>` або `Refs #<issue_id>`
  **FR-PR-002**: При відкритті PR встановити `Status=Review`.

### 7.7 Sync статусів

**FR-SYNC-001**: Якщо issue закрито (або merge PR з closing keyword), skill має встановити `Status=Done`.

---

## 8. Нефункціональні вимоги

### 8.1 Надійність і повторний запуск

* Усі операції **idempotent**.
* Повторний bootstrap не створює дублікати labels/fields/views.

### 8.2 Безпека

* Токен зберігати в IDE secret storage.
* Мінімальні дозволи:

  * repo: read/write для labels, contents, issues
  * projects v2: read/write (user project)
* Логи не повинні містити токенів/секретів.

### 8.3 UX

* Bootstrap: один екран + “dry run” (показати план змін).
* Commit assistant: 5–10 секунд на заповнення, мінімум полів.
* Не блокувати коміт без крайньої потреби: блокувати лише якщо `enforce_issue_link=true`.

### 8.4 Продуктивність

* Кешувати:

  * список labels
  * список open issues
  * project id і field ids
* Обмежити частоту API викликів (rate limit).

---

## 9. Дані та моделі

### Внутрішні сутності

* `RepoConfig`
* `BootstrapPlan` (список дій + expected/noop)
* `IssueRef {id, number, title, url}`
* `ProjectRef {id, title, fields{status_id, priority_id}}`
* `SyncQueueItem` (offline actions)

---

## 10. Інтеграції з GitHub API

### REST

* Репозиторій: GET/PATCH settings
* Labels: list/create/update
* Contents API: create/update файлів `.github/*`
* Issues: list/create/read

### GraphQL (Projects v2 user-level)

* Отримати user ID
* List projects (з фільтрацією по назві)
* Create project
* Create/update fields (single select)
* Add item (issue) to project
* Update item field values

> Реалізаційно важливо: після створення Project і полів зберегти їхні `node_id`/`field_id` у кеші.

---

## 11. IDE інтеграція (UI/Commands)

### Команди

* `GitHub: Bootstrap Repository`
* `GitHub: Create Issue (Task/Bug)`
* `GitHub: Create Branch from Issue`
* `GitHub: Commit with Assistant`
* `GitHub: Create PR with Assistant`
* `GitHub: Sync Pending Actions`

### UI

* Bootstrap wizard:

  * показ “що буде змінено”
  * кнопки: Run / Dry-run / Cancel
* Commit assistant modal:

  * type dropdown
  * scope input
  * subject input
  * issue selector (search open issues)
  * preview commit message

---

## 12. Правила комітів (мінімум)

### Формат

`<type>(<scope>): <subject> #<issue_id>`

Приклади:

* `feat(updater): check latest.json and prompt install #17`
* `fix(db): add index for results_year_agegroup #23`

Валідації:

* `type` ∈ allowed_types
* `subject` 5..72 символи, без крапки в кінці
* `#issue_id` обов’язково, якщо enforce увімкнено

---

## 13. План тестування

### Unit

* Парсинг issue_id з branch name
* Генерація commit message
* Idempotent merge для labels/files

### Integration

* Bootstrap на пустому репо
* Bootstrap повторно (усе `noop`)
* Створення issue і додавання в Project
* Commit assistant: перший коміт → статус `In progress`
* PR відкритий → статус `Review`
* Merge з `Fixes #ID` → статус `Done`

### Negative

* Немає токена → коректне повідомлення
* Rate limit → retry/backoff
* Offline → queue + sync

---

## 14. Логи і спостережуваність

* Логувати:

  * виконані дії (created/updated/noop)
  * помилки API з кодом відповіді
* Не логувати секрети.
* Опційно: telemetry вимкнена за замовчуванням.

---

## 15. Критерії приймання (Acceptance Criteria)

1. Bootstrap:

* На чистому репо створені labels, шаблони `.github/*`, PR template.
* Створений user-level Project `Work` з полями `Status` і `Priority`.
* Повторний запуск не створює дублікатів.

2. Commit assistant:

* При коміті без issue_id (і enforce=true) — skill вимагає вибір issue або відмовляє.
* При першому коміті по issue — issue додається у Project і стає `In progress`.
* Коміт має формат і проходить валідацію.

3. PR assistant (якщо ввімкнено):

* PR містить шаблон і посилання на issue.
* Статус у Project переходить у `Review`.

---

## 16. Ризики і рішення

* **Projects v2 складніші за REST** → зафіксувати мінімальний набір GraphQL операцій і кешувати IDs.
* **Rate limit** → кеш + exponential backoff.
* **Offline** → локальний queue для синхронізації.

---

## 17. Deliverables (що саме здати)

1. Skill/плагін для IDE з командами (розділ 11).
2. Конфіг-файл `repo-skill.yml` + документація полів.
3. Реалізація Bootstrap (REST + GraphQL).
4. Реалізація Commit assistant (UI + validations + API sync).
5. Набір шаблонів (issue/PR/CODEOWNERS) як ресурси пакета.
6. Тестовий репозиторій + сценарії перевірки.

---

## 18. MVP-обсяг (рекомендовано)

Якщо хочеш швидко в production:

* Bootstrap (settings + labels + templates + Project + fields)
* Commit assistant (issue link + commit message generator)
* Синхронізація `In progress` на перший коміт
* Без PR assistant і без offline queue (це v1.1)

---

Якщо скажеш **яка саме IDE** (JetBrains / VS Code / Windsurf / інша) і **який формат “skill” у твоєму IDE** (команда + JSON schema / YAML / TypeScript), я адаптую ТЗ під конкретний runtime (точні entrypoints, storage для токенів, hook lifecycle).

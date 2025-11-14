# Document Flow Management System

## Статистика проекта

- **Всего классов:** 72
- **Всего полей:** 170
- **Всего методов:** 142
- **Классов-исключений:** 12
- **Ассоциаций между классами:** 33

## Описание

Система управления документооборотом с поддержкой:
- Управление пользователями и ролями
- Работа с документами и их версионирование
- Маршруты согласования документов
- Система безопасности и аутентификации
- Платежные операции
- Хранение и архивирование документов

---

## Модули системы

### Модуль: `cli.py`

#### `DemoContext`

**Поля:**

- `repo: InMemoryDocumentRepository`
- `storage: DocumentStorage`
- `doc_service: DocumentService`
- `appr_service: ApprovalService`
- `pay_service: PaymentService`
- `auth: AuthService`

---

### Модуль: `core.py`

#### `BaseEntity`

**Поля:**

- `created_at: datetime`
- `updated_at: datetime`

**Методы:**

- `touch()`

---

#### `IdentifiableMixin`

**Поля:**

- `id: str`

**Методы:**

- `identity()`

---

#### `TimestampMixin`

**Поля:**

- `created_at: datetime`
- `updated_at: datetime`

---

#### `Validatable`

**Методы:**

- `validate()`

---

#### `Approvable`

**Методы:**

- `approve()`

---

#### `Signable`

**Методы:**

- `sign(user_id)`

---

#### `Storable`

**Методы:**

- `store()`

---

#### `NotifierProtocol`

**Методы:**

- `notify(message)`

---

#### `PaymentProcessorProtocol`

**Методы:**

- `transfer(src_account, dst_account, amount)`

---

#### `DocumentLike`

**Поля:**

- `number: str`
- `title: str`

**Методы:**

- `validate()`

---

#### `DocumentRepositoryProtocol`

**Методы:**

- `save(doc)`
- `get(number)`
- `exists(number)`
- `search(query)`

---

### Модуль: `documents.py`

#### `DocumentMetadata`

**Поля:**

- `tags: List[str]`
- `attributes: Dict[str, str]`

**Методы:**

- `add_tag(tag)`: Add a tag to metadata
- `remove_tag(tag)`: Remove a tag from metadata
- `has_tag(tag)`: Check if metadata has a specific tag

---

#### `DocumentAttachment`

**Поля:**

- `filename: str`
- `content_type: str`
- `size: int`
- `checksum: str`

**Методы:**

- `is_image()`: Check if attachment is an image
- `is_pdf()`: Check if attachment is a PDF
- `get_extension()`: Get file extension

---

#### `DocumentVersion`

**Поля:**

- `number: int`
- `content: str`
- `created_at: datetime`
- `author_id: str`
- `comment: str`

**Методы:**

- `get_content_length()`: Get content length
- `is_latest(total_versions)`: Check if this is the latest version

---

#### `Signature`

**Поля:**

- `user_id: str`
- `certificate_id: str`
- `signed_at: datetime`

**Методы:**

- `is_valid_for(user_id)`: Check if signature belongs to user

---

#### `DigitalCertificate`

**Поля:**

- `id: str`
- `subject: str`
- `valid_from: datetime`
- `valid_to: datetime`
- `issuer: str`

**Методы:**

- `is_valid(moment)`
- `days_until_expiry()`: Get days until certificate expires
- `is_expiring_soon(days)`: Check if certificate is expiring within specified days

---

#### `DocumentHistoryRecord`

**Поля:**

- `event: str`
- `actor_id: str`
- `occurred_at: datetime`
- `details: str`

**Методы:**

- `get_event_type()`: Get event type

---

#### `DocumentLock`

**Поля:**

- `owner_id: str`
- `acquired_at: datetime`

**Методы:**

- `get_lock_duration()`: Get lock duration in seconds

---

#### `Document`

**Поля:**

- `id: str`
- `number: str`
- `title: str`
- `author: User`
- `organization: Organization | None`
- `department: Department | None`
- `status: str`
- `versions: List[DocumentVersion]`
- `attachments: List[DocumentAttachment]`
- `approval_route: ApprovalRoute | None`
- `metadata: DocumentMetadata`
- `signatures: List[Signature]`

**Методы:**

- `validate()`
- `add_version(content, author_id)`
- `add_attachment(attachment)`
- `lock(user_id)`
- `unlock(user_id)`
- `approve()`
- `sign(user_id)`
- `archive()`
- `restore()`

---

#### `IncomingDocument`

**Поля:**

- `sender: str`

**Методы:**

- `approve()`

---

#### `OutgoingDocument`

**Поля:**

- `recipient: str`

**Методы:**

- `approve()`

---

#### `ContractDocument`

**Поля:**

- `effective_from: datetime | None`
- `effective_to: datetime | None`
- `total_amount: int`

**Методы:**

- `validate()`

---

#### `InvoiceDocument`

**Поля:**

- `amount_due: int`
- `due_date: datetime | None`
- `paid: bool`

**Методы:**

- `mark_paid()`

---

#### `OrderDocument`

**Поля:**

- `items: List[str]`

---

#### `DocumentRegistry`

**Поля:**

- `numbers: set[str]`

**Методы:**

- `register(number)`
- `contains(number)`
- `unregister(number)`: Unregister a document number
- `count()`: Count registered numbers

---

### Модуль: `exceptions.py`

#### `DocumentNotFoundError` (Исключение)

Пользовательское исключение для обработки ошибок.

---

#### `InvalidDocumentStatusError` (Исключение)

Пользовательское исключение для обработки ошибок.

---

#### `AccessDeniedError` (Исключение)

Пользовательское исключение для обработки ошибок.

---

#### `ApprovalStepError` (Исключение)

Пользовательское исключение для обработки ошибок.

---

#### `InvalidSignatureError` (Исключение)

Пользовательское исключение для обработки ошибок.

---

#### `UserBlockedError` (Исключение)

Пользовательское исключение для обработки ошибок.

---

#### `VersionConflictError` (Исключение)

Пользовательское исключение для обработки ошибок.

---

#### `RouteNotFoundError` (Исключение)

Пользовательское исключение для обработки ошибок.

---

#### `PaymentOperationError` (Исключение)

Пользовательское исключение для обработки ошибок.

---

#### `AuthFailedError` (Исключение)

Пользовательское исключение для обработки ошибок.

---

#### `DuplicateDocumentError` (Исключение)

Пользовательское исключение для обработки ошибок.

---

#### `StorageLimitExceededError` (Исключение)

Пользовательское исключение для обработки ошибок.

---

### Модуль: `payments.py`

#### `Currency`

---

#### `Account`

**Поля:**

- `number: str`
- `currency: str`
- `balance: int`
- `is_frozen: bool`
- `overdraft_limit: int`

**Методы:**

- `debit(amount)`
- `credit(amount)`
- `freeze()`: Freeze account operations
- `unfreeze()`: Unfreeze account operations
- `set_overdraft_limit(limit)`: Set overdraft limit for the account
- `get_available_balance()`: Get available balance including overdraft

---

#### `Transaction`

**Поля:**

- `id: str`
- `src: str`
- `dst: str`
- `amount: int`
- `created_at: datetime`
- `status: str`
- `description: str`

**Методы:**

- `cancel()`: Mark transaction as cancelled
- `is_completed()`: Check if transaction is completed

---

#### `PaymentOrder`

**Поля:**

- `invoice_number: str`
- `src_account: str`
- `dst_account: str`
- `amount: int`
- `currency: str`
- `priority: int`
- `scheduled_date: datetime | None`

**Методы:**

- `is_high_priority()`: Check if this is a high priority payment
- `is_scheduled()`: Check if payment is scheduled for future

---

#### `BalanceChecker`

**Поля:**

- `min_balance: int`

**Методы:**

- `ensure_same_currency(a, b)`
- `check_sufficient_funds(account, amount)`: Check if account has sufficient funds
- `check_min_balance(account)`: Check if account meets minimum balance requirement

---

#### `InMemoryPaymentProcessor`

**Поля:**

- `accounts: Dict[str, Account]`
- `balance_checker: BalanceChecker`
- `transactions: List[Transaction]`
- `daily_limit: int`

**Методы:**

- `transfer(src_account, dst_account, amount)`
- `get_account_balance(account_number)`: Get account balance
- `get_transaction_history(account_number)`: Get transaction history for account
- `check_daily_limit(amount)`: Check if amount is within daily limit

---

### Модуль: `security.py`

#### `PasswordPolicy`

**Поля:**

- `min_length: int`
- `require_digit: bool`
- `require_uppercase: bool`
- `require_special: bool`

**Методы:**

- `validate(password)`
- `get_strength_score(password)`: Calculate password strength score (0-100)

---

#### `Session`

**Поля:**

- `user_id: str`
- `token: str`
- `created_at: datetime`
- `expires_at: datetime`
- `ip_address: str`
- `is_terminated: bool`

**Методы:**

- `is_active(moment)`
- `terminate()`: Terminate this session
- `extend(hours)`: Extend session expiration time

---

#### `Token`

**Поля:**

- `value: str`
- `issued_at: datetime`
- `expires_at: datetime | None`

**Методы:**

- `generate()`
- `is_expired(moment)`: Check if token is expired
- `revoke()`: Revoke token by setting expiration to now

---

#### `QuotaManager`

**Поля:**

- `max_bytes: int`
- `used_bytes: int`
- `warning_threshold: int`

**Методы:**

- `can_allocate(size)`
- `allocate(size)`
- `deallocate(size)`: Free up quota space
- `get_usage_percentage()`: Get quota usage as percentage
- `is_near_limit()`: Check if usage is near warning threshold

---

### Модуль: `services.py`

#### `InMemoryDocumentRepository`

**Поля:**

- `storage: DocumentStorage`

**Методы:**

- `save(doc)`
- `get(number)`
- `exists(number)`
- `search(query)`

---

#### `ConsoleNotifier`

**Методы:**

- `notify(message)`

---

#### `SearchService`

**Поля:**

- `repo: DocumentRepositoryProtocol`

**Методы:**

- `find(query)`

---

#### `ValidationService`

**Методы:**

- `validate(doc)`

---

#### `NotificationService`

**Поля:**

- `notifier: NotifierProtocol`

**Методы:**

- `send(message)`

---

#### `DocumentService`

**Поля:**

- `repo: DocumentRepositoryProtocol`
- `registry: DocumentRegistry`
- `validator: ValidationService`
- `notifier: NotificationService`

**Методы:**

- `register(doc)`
- `add_attachment(number, att)`
- `send_for_approval(number, route)`
- `sign(number, user)`
- `archive(number)`
- `require(number)`

---

#### `ApprovalService`

**Поля:**

- `notifier: NotificationService`

**Методы:**

- `route_for_role(role_name)`
- `approve(doc)`

---

#### `PaymentService`

**Поля:**

- `processor: PaymentProcessorProtocol`
- `notifier: NotificationService`

**Методы:**

- `pay_invoice(invoice, src, dst, amount)`

---

#### `AuthService`

**Поля:**

- `users: Dict[str, str]`
- `policy: PasswordPolicy`

**Методы:**

- `login(login, password)`

---

### Модуль: `storage.py`

#### `StorageLocation`

**Поля:**

- `name: str`
- `base_path: str`
- `is_active: bool`
- `capacity: int`

**Методы:**

- `validate_path()`: Validate that path is not empty
- `get_full_path(filename)`: Get full path to file

---

#### `DocumentStorage`

**Поля:**

- `location: StorageLocation`
- `quota: QuotaManager`

**Методы:**

- `save(doc)`
- `get(number)`
- `exists(number)`
- `store_attachment(doc, att)`
- `archive(doc)`
- `delete(number)`: Delete document from storage
- `count_documents()`: Count total documents in storage
- `get_all_numbers()`: Get all document numbers
- `clear()`: Clear all documents from storage

---

#### `ArchiveService`

**Поля:**

- `storage: DocumentStorage`
- `archive_retention_days: int`

**Методы:**

- `archive_document(number)`
- `restore_document(number)`
- `get_archived_documents()`: Get all archived documents
- `can_delete_archived(doc)`: Check if archived document can be permanently deleted

---

### Модуль: `users.py`

#### `Permission`

**Поля:**

- `code: str`
- `description: str`
- `priority: int`

**Методы:**

- `is_higher_priority_than(other)`: Check if this permission has higher priority than another

---

#### `Role`

**Поля:**

- `name: str`
- `permissions: Set[Permission]`
- `is_active: bool`

**Методы:**

- `allows(code)`
- `add_permission(permission)`: Add a permission to this role
- `remove_permission(permission)`: Remove a permission from this role
- `deactivate()`: Deactivate this role
- `activate()`: Activate this role

---

#### `Department`

**Поля:**

- `name: str`
- `cost_center: str`
- `budget: int`
- `head_id: str`

**Методы:**

- `allocate_budget(amount)`: Allocate budget to department
- `spend_budget(amount)`: Spend budget from department. Returns True if successful
- `get_remaining_budget()`: Get remaining budget

---

#### `AccessPolicy`

**Поля:**

- `allowed_roles: Set[str]`
- `denied_roles: Set[str]`

**Методы:**

- `can_access(roles)`
- `allow_role(role_name)`: Allow a role in this policy
- `deny_role(role_name)`: Deny a role in this policy

---

#### `Organization`

**Поля:**

- `name: str`
- `inn: str`
- `address: str`
- `phone: str`
- `email: str`

**Методы:**

- `update_contact_info(phone, email)`: Update organization contact information
- `validate_inn()`: Validate INN (Tax Identification Number)

---

#### `User`

**Поля:**

- `id: str`
- `login: str`
- `display_name: str`
- `is_blocked: bool`
- `roles: List[Role]`
- `department: Department | None`
- `org: Organization | None`
- `email: str`
- `phone: str`

**Методы:**

- `has_permission(code)`
- `assign_role(role)`
- `remove_role(role)`: Remove a role from user
- `block()`: Block user access
- `unblock()`: Unblock user access
- `change_department(department)`: Change user's department
- `get_active_roles()`: Get list of active roles

---

### Модуль: `workflow.py`

#### `WorkflowState`

---

#### `ApprovalStep`

**Поля:**

- `name: str`
- `role_name: str`
- `required: bool`
- `deadline_hours: int`
- `order: int`

**Методы:**

- `deadline(start)`
- `is_overdue(start)`: Check if step is overdue
- `extend_deadline(additional_hours)`: Extend deadline by additional hours

---

#### `ApprovalTask`

**Поля:**

- `step: ApprovalStep`
- `assignee_id: str`
- `created_at: datetime`
- `completed: bool`
- `comment: str`
- `completed_at: datetime | None`

**Методы:**

- `complete(comment)`
- `reassign(new_assignee_id)`: Reassign task to another user
- `is_overdue()`: Check if task is overdue

---

#### `ApprovalRoute`

**Поля:**

- `name: str`
- `steps: List[ApprovalStep]`
- `is_active: bool`

**Методы:**

- `first_step()`
- `next_step(current)`
- `add_step(step)`: Add a step to the route
- `remove_step(step)`: Remove a step from the route
- `get_step_count()`: Get total number of steps

---

#### `WorkflowTransition`

**Поля:**

- `src: str`
- `dst: str`
- `reason: str`
- `actor_id: str`
- `timestamp: datetime`

**Методы:**

- `is_valid_transition()`: Check if this is a valid state transition

---

#### `Notification`

**Поля:**

- `message: str`
- `recipient_id: str`
- `created_at: datetime`
- `is_read: bool`
- `priority: int`

**Методы:**

- `mark_read()`: Mark notification as read
- `is_high_priority()`: Check if notification is high priority

---

## Исключения

Система использует следующие пользовательские исключения:

1. `AccessDeniedError`
2. `ApprovalStepError`
3. `AuthFailedError`
4. `DocumentNotFoundError`
5. `DuplicateDocumentError`
6. `InvalidDocumentStatusError`
7. `InvalidSignatureError`
8. `PaymentOperationError`
9. `RouteNotFoundError`
10. `StorageLimitExceededError`
11. `UserBlockedError`
12. `VersionConflictError`

## Ассоциации между классами

Система включает следующие ассоциации (связи между классами):

1. AccessPolicy → List[Role] (method parameter)
2. ApprovalRoute → ApprovalStep (field steps)
3. ApprovalRoute → ApprovalStep (method parameter)
4. ApprovalService → Document (method parameter)
5. ArchiveService → Document (method parameter)
6. ArchiveService → DocumentStorage (field storage)
7. BalanceChecker → Account (method parameter)
8. DemoContext → DocumentStorage (field storage)
9. Document → Document (field attachments)
10. Document → Document (field versions)
11. Document → DocumentAttachment (field attachments)
12. Document → DocumentAttachment (method parameter)
13. Document → Signature (field signatures)
14. Document → User (field author)
15. DocumentService → ApprovalRoute (method parameter)
16. DocumentService → Document (method parameter)
17. DocumentService → DocumentAttachment (method parameter)
18. DocumentService → User (method parameter)
19. DocumentStorage → Document (method parameter)
20. DocumentStorage → DocumentAttachment (method parameter)
21. DocumentStorage → QuotaManager (field quota)
22. InMemoryDocumentRepository → Document (method parameter)
23. InMemoryDocumentRepository → DocumentStorage (field storage)
24. InMemoryPaymentProcessor → Account (field accounts)
25. InMemoryPaymentProcessor → BalanceChecker (field balance_checker)
26. InMemoryPaymentProcessor → Transaction (field transactions)
27. PaymentService → InvoiceDocument (method parameter)
28. Role → Permission (field permissions)
29. Role → Permission (method parameter)
30. User → Department (method parameter)

**Всего уникальных ассоциаций:** 30

## Ключевые возможности

### Управление пользователями
- Создание и управление пользователями
- Система ролей и разрешений
- Блокировка/разблокировка пользователей
- Управление департаментами и организациями

### Документооборот
- Создание и редактирование документов
- Версионирование документов
- Вложения к документам
- Цифровые подписи
- Блокировка документов для редактирования
- Архивирование и восстановление

### Согласование
- Создание маршрутов согласования
- Назначение задач на согласование
- Отслеживание статусов
- Уведомления о событиях

### Безопасность
- Аутентификация пользователей
- Политики паролей
- Управление сессиями и токенами
- Контроль квот хранилища

### Платежи
- Переводы между счетами
- Проверка баланса и валюты
- История транзакций
- Контроль лимитов
- Заморозка/разморозка счетов



## Структура проекта

```
lab2/
├── documentflow/          # Основной пакет
│   ├── core.py           # Базовые классы и протоколы
│   ├── users.py          # Пользователи и роли
│   ├── documents.py      # Документы и вложения
│   ├── workflow.py       # Маршруты согласования
│   ├── security.py       # Безопасность
│   ├── payments.py       # Платежные операции
│   ├── storage.py        # Хранилище документов
│   ├── services.py       # Сервисы приложения
│   └── exceptions.py     # Пользовательские исключения
├── tests/                # Тесты
└── main.py              # Точка входа
```

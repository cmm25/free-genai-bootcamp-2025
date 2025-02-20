# BACKEND SERVER TECHNICAL SPECS.

## BUSINESS GOAL:
A language learning school aims to develop a prototype learning portal that serves three primary functions:

- **Vocabulary Repository:** A comprehensive inventory of vocabulary available for study.
- **Learning Record Store (LRS):** A system to track and analyze practice performance, recording both correct and incorrect responses.
- **Unified Launchpad:** A centralized gateway for launching various interactive learning applications.

## TECHNICAL REQUIREMENTS.

- The backend is built using Python.
- The database will be SQLite3.
- The API will be built using Django.
- Desired API output is JSON.
- The will be no authentication or authorization.
- One user **(Super user)**.

## DIRECTORY STRUCTURE.

```text
backend_django/
├── manage.py                         # Django's command-line utility
├── learning_portal/                  # Project configuration folder
│   ├── __init__.py
│   ├── settings.py                   
│   ├── urls.py                       # Global URL configuration
│   └── wsgi.py
└── portal/                           # Main app for language learning features
    ├── __init__.py
    ├── admin.py                      # Admin site configuration
    ├── models.py                     # Database models for vocabulary and learning records
    ├── serializers.py                # Serializers for API data conversion (e.g., using Django REST Framework)
    ├── views.py                      # HTTP request handlers (views) for API endpoints
    ├── urls.py                       # App-specific URL patterns
    ├── tests.py                      # Test cases 
    └── migrations/                   # Auto-generated database migrations
        └── __init__.py
```

## DATABASE SCHEMA.

The database will be a single SQLITE database normally provided by Django that will be in the root of the project folder.
Below are models representing the tables of the database schema:

### Words

| Column   | Type    | Description                                      |
|----------|---------|--------------------------------------------------|
| id       | integer | Primary key                                      |
| japanese | string  | Vocabulary word in Japanese                      |
| romaji   | string  | Transliterated version in Romaji                 |
| english  | string  | English translation                              |
| parts    | json    | Additional parts information stored as JSON      |

### Words_Groups

| Column   | Type    | Description                                       |
|----------|---------|---------------------------------------------------|
| id       | integer | Primary key                                       |
| word_id  | integer | Foreign key referencing **Words**               |
| group_id | integer | Foreign key referencing **Groups**              |

### Groups

| Column | Type    | Description                       |
|--------|---------|-----------------------------------|
| id     | integer | Primary key                       |
| name   | string  | Thematic group of words           |

### Study_Sessions

| Column            | Type     | Description                                                       |
|-------------------|----------|-------------------------------------------------------------------|
| id                | integer  | Primary key                                                       |
| group_id          | integer  | Foreign key referencing **Groups**                                |
| created_at        | datetime | Date and time the study session was created                       |
| study_activity_id | integer  | Foreign key linking to **Study_Activities** (if applicable)         |

### Study_Activities

| Column           | Type     | Description                                                      |
|------------------|----------|------------------------------------------------------------------|
| id               | integer  | Primary key                                                      |
| study_session_id | integer  | Foreign key referencing **Study_Sessions**                       |
| group_id         | integer  | Foreign key referencing **Groups**                               |
| created_at       | datetime | Date and time the study activity was created                     |

### Word_Review_Items

| Column           | Type     | Description                                                      |
|------------------|----------|------------------------------------------------------------------|
| word_id          | integer  | Foreign key referencing **Words**                                |
| study_session_id | integer  | Foreign key referencing **Study_Sessions**                       |
| correct          | boolean  | Indicates whether the word was answered correctly                |
| created_at       | datetime | Date and time the review item was created                        |
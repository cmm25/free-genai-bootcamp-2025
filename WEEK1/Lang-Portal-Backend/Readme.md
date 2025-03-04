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

| Column   | Type    | Description                                 |
| -------- | ------- | ------------------------------------------- |
| id       | integer | Primary key                                 |
| japanese | string  | Vocabulary word in Japanese                 |
| romaji   | string  | Transliterated version in Romaji            |
| english  | string  | English translation                         |
| parts    | json    | Additional parts information stored as JSON |

### Words_Groups

| Column   | Type    | Description                        |
| -------- | ------- | ---------------------------------- |
| id       | integer | Primary key                        |
| word_id  | integer | Foreign key referencing **Words**  |
| group_id | integer | Foreign key referencing **Groups** |

### Groups

| Column | Type    | Description             |
| ------ | ------- | ----------------------- |
| id     | integer | Primary key             |
| name   | string  | Thematic group of words |

### Study_Sessions

| Column            | Type     | Description                                                 |
| ----------------- | -------- | ----------------------------------------------------------- |
| id                | integer  | Primary key                                                 |
| group_id          | integer  | Foreign key referencing **Groups**                          |
| created_at        | datetime | Date and time the study session was created                 |
| study_activity_id | integer  | Foreign key linking to **Study_Activities** (if applicable) |

### Study_Activities

| Column           | Type     | Description                                  |
| ---------------- | -------- | -------------------------------------------- |
| id               | integer  | Primary key                                  |
| study_session_id | integer  | Foreign key referencing **Study_Sessions**   |
| group_id         | integer  | Foreign key referencing **Groups**           |
| created_at       | datetime | Date and time the study activity was created |

### Word_Review_Items

| Column           | Type     | Description                                       |
| ---------------- | -------- | ------------------------------------------------- |
| word_id          | integer  | Foreign key referencing **Words**                 |
| study_session_id | integer  | Foreign key referencing **Study_Sessions**        |
| correct          | boolean  | Indicates whether the word was answered correctly |
| created_at       | datetime | Date and time the review item was created         |

## API ENDPOINTS DOCUMENTATION

### Base URL
All API endpoints are prefixed with `/api/`

### Dashboard Endpoints

#### Get Last Study Session
```
GET /api/dashboard/last_study_session/
```

#### Get Study Progress
```
GET /api/dashboard/study_progress/
Query Parameters:
- group_id (optional): Filter progress for specific group
```

#### Get Quick Stats
```
GET /api/dashboard/quick-stats/
```

### Word Endpoints

#### List/Create Words
```
GET, POST /api/words/
Query Parameters:
- search: Search words by Swahili or English text
- page: Page number for pagination
- items_per_page: Number of items per page (default: 100)
```

#### Get/Update/Delete Word
```
GET, PUT, DELETE /api/words/:id/
```

#### Get Word Stats
```
GET /api/words/:id/stats/
```

### Group Endpoints

#### List/Create Groups
```
GET, POST /api/groups/
Query Parameters:
- category: Filter groups by category
- page: Page number for pagination
```

#### Get/Update/Delete Group
```
GET, PUT, DELETE /api/groups/:id/
```

#### List Group Words
```
GET /api/groups/:id/words/
```

#### List Group Study Sessions
```
GET /api/groups/:id/study_sessions/
```

### Study Activities Endpoints

#### Create Study Activity
```
POST /api/study_activities/
```

#### Get Study Activity
```
GET /api/study_activities/:id/
```

#### List Activity Sessions
```
GET /api/study_activities/:id/study_sessions/
```

### Study Sessions Endpoints

#### List/Create Sessions
```
GET, POST /api/study_sessions/
```

#### Get/Update/Delete Session
```
GET, PUT, DELETE /api/study_sessions/:id/
```

#### List Session Words
```
GET /api/study_sessions/:id/words/
```

### System Management Endpoints

#### Reset Study History
```
POST /api/reset_history/
```

#### Full System Reset
```
POST /api/full_reset/
```

### Error Responses

All endpoints may return the following error responses:

#### Not Found (404)
```json
{
    "error": "Resource not found"
}
```

#### Bad Request (400)
```json
{
    "error": "Invalid request parameters"
}
```

#### Server Error (500)
```json
{
    "error": "Internal server error"
}
```

## Testing with Postman

1. Base URL: `http://localhost:8000/api/`
2. No authentication required
3. All responses are in JSON format
4. Use the provided example responses to validate your API responses

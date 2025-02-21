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

Response 200:
{
    "id": 123,
    "group_id": 456,
    "created_at": "2024-03-14T12:00:00Z",
    "study_activity_id": 789,
    "group_name": "Basic Greetings"
}
```

#### Get Study Progress

```
GET /api/dashboard/study_progress/

Response 200:
{
    "current_group": {
        "id": 1,
        "name": "Basic Greetings",
        "total_words": 50,
        "words_studied": 30,
        "progress_percentage": 60.0,
        "total_reviews": 100,
        "correct_reviews": 85,
        "accuracy": 85.0
    },
    "all_groups_progress": [
        {
            "group_id": 1,
            "group_name": "Basic Greetings",
            "total_words": 50,
            "words_studied": 30,
            "progress_percentage": 60.0,
            "accuracy": 85.0
        }
    ],
    "overall_progress": {
        "total_words_studied": 45,
        "total_available_words": 100,
        "overall_progress_percentage": 45.0
    }
}
```

#### Get Quick Stats

```
GET /api/dashboard/quick-stats/

Response 200:
{
    "success_rate": 85.0,
    "total_study_sessions": 25,
    "total_active_groups": 3,
    "study_streak_days": 5
}
```

### Word Endpoints

#### List Words

```
GET /api/words/

Parameters:
- page (optional): Page number for pagination
- items_per_page (optional): Number of items per page (default: 100)

Response 200:
{
    "items": [
        {
            "id": 1,
            "Swahili": "jambo",
            "Pronounciation": "jahm-boh",
            "English": "hello",
            "correct_count": 10,
            "wrong_count": 2,
            "categories": [
                {
                    "id": 1,
                    "name": "Greetings",
                    "description": "Basic greetings"
                }
            ],
            "groups": [
                {
                    "id": 1,
                    "name": "Basic Greetings",
                    "stats": {
                        "correct_count": 8,
                        "wrong_count": 1
                    }
                }
            ]
        }
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 5,
        "total_items": 500,
        "items_per_page": 100
    }
}
```

#### Get Word Stats

```
GET /api/words/:id/stats/

Response 200:
{
    "word": {
        "id": 1,
        "swahili": "jambo",
        "english": "hello"
    },
    "stats": {
        "total_reviews": 12,
        "correct_reviews": 10,
        "accuracy": 83.33
    }
}
```

### Group Endpoints

#### List Groups

```
GET /api/groups/

Response 200:
{
    "items": [
        {
            "id": 1,
            "name": "Basic Greetings",
            "description": "Common greetings in Swahili",
            "word_count": 20,
            "stats": {
                "total_word_count": 20,
                "sessions_count": 5,
                "progress": {
                    "total_words": 20,
                    "words_studied": 15,
                    "progress_percentage": 75.0,
                    "total_reviews": 45,
                    "correct_reviews": 38,
                    "accuracy": 84.4
                },
                "category_distribution": {
                    "Nouns": 8,
                    "Verbs": 5,
                    "Expressions": 7
                }
            },
            "categories": [
                {
                    "id": 1,
                    "name": "Beginner",
                    "description": "Beginner level words"
                }
            ]
        }
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 1,
        "total_items": 10,
        "items_per_page": 100
    }
}
```

### Study Session Endpoints

#### List Study Sessions

```
GET /api/study_sessions/

Response 200:
{
    "items": [
        {
            "id": 123,
            "activity_name": "Vocabulary Quiz",
            "group_name": "Basic Greetings",
            "creation_time": "2024-03-14T12:00:00Z",
            "end_time": "2024-03-14T12:15:00Z",
            "review_items_count": 20,
            "duration": 900
        }
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 5,
        "total_items": 100,
        "items_per_page": 100
    }
}
```

#### Create Word Review

```
POST /api/study_sessions/:id/words/:word_id/review/

Request Body:
{
    "correct": true
}

Response 200:
{
    "success": true,
    "word_id": 1,
    "study_session_id": 123,
    "correct": true,
    "created_at": "2024-03-14T12:10:00Z"
}
```

### System Reset Endpoints

#### Reset Study History

```
POST /api/reset_history/

Response 200:
{
    "success": true,
    "message": "Study history has been reset"
}
```

#### Full System Reset

```
POST /api/full_reset/

Response 200:
{
    "success": true,
    "message": "System has been fully reset"
}
```

### Error Responses

All endpoints may return the following error responses:

#### Not Found (404)

```
{
    "error": "Resource not found"
}
```

#### Bad Request (400)

```
{
    "error": "Invalid request parameters"
}
```

#### Server Error (500)

```
{
    "error": "Internal server error"
}
```

## Testing with Postman

1. Import the collection using this link: [Postman Collection Link]
2. Set up environment variables:
   - `base_url`: Your server URL (e.g., `http://localhost:8000`)
3. All endpoints are prefixed with `/api/`
4. No authentication is required
5. Use the provided example responses to validate your API responses

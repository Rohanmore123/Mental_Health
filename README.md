# Mental Health Care System

A comprehensive healthcare management system with doctor recommendations, AI chat, and mood analysis.

## Features

- User authentication and role-based access control
- Doctor recommendation system
- AI-powered chat (text and audio)
- Mood and sentiment analysis dashboard
- Appointment management
- Medical records and prescriptions

## Tech Stack

### Backend
- **Framework**: FastAPI
- **Database ORM**: SQLAlchemy
- **Data Validation**: Pydantic
- **Database**: PostgreSQL
- **AI Services**: OpenAI API
- **Authentication**: JWT

### Frontend
- **HTML/CSS/JavaScript**
- **Bootstrap 5** for responsive design
- **Font Awesome** for icons
- **Jinja2** for templating

## Setup and Installation

### Prerequisites

- Python 3.8+
- PostgreSQL database
- OpenAI API key (optional for AI chat features)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/Rohanmore123/Mental_Health.git
   cd Mental_Health
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure the `.env` file with your database connection and other settings:
   ```
   # Application settings
   DEBUG=True

   # Database settings
   DATABASE_URL=postgresql://postgres:Raje%4012345@localhost:5432/Prasha_care

   # JWT Authentication settings
   SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # OpenAI settings
   OPENAI_API_KEY=your-openai-api-key-here
   ```

5. Initialize the database:
   ```
   python init_db.py
   ```

6. Seed the database with initial data:
   ```
   python seed_db.py
   ```

7. Start the development server:
   ```
   python run.py
   ```

## Using the Application

Once the server is running, you can access the application at:

- Home page: `http://localhost:8000/`
- Login page: `http://localhost:8000/login`
- Mobile login: `http://localhost:8000/mobile-login`

### Default Login Credentials

#### Test User
- Email: test@example.com
- Password: Raje@12345

## API Documentation

The API documentation is available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
Mental_Health/
├── app/
│   ├── api/              # API endpoints
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── static/           # Static files (CSS, JS, images)
│   ├── templates/        # HTML templates
│   ├── utils/            # Utility functions
│   ├── config.py         # Configuration settings
│   ├── database.py       # Database connection
│   └── main.py           # FastAPI application
├── alembic/              # Database migrations
├── .env                  # Environment variables
├── init_db.py            # Database initialization script
├── seed_db.py            # Database seeding script
├── requirements.txt      # Project dependencies
└── run.py                # Application runner
```

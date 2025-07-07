# Creatist Backend

A FastAPI-based backend for the Creatist application with vision board management, user authentication, and collaboration features.

## Features

- **User Management**: Authentication, profiles, following system
- **Vision Boards**: Create, manage, and collaborate on vision boards
- **Role-based Assignments**: Assign different roles (videographer, photographer, etc.)
- **Real-time Communication**: Messaging and notifications
- **Showcase Management**: Portfolio and work showcase features

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL database (via Supabase)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd creatist-backend
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file with the following variables:
   ```env
   HOST="0.0.0.0"
   PORT="8080"
   JWT_SECRET="your-jwt-secret"
   SUPABASE_URL="your-supabase-url"
   SUPABASE_KEY="your-supabase-key"
   EMAIL_ADDRESS="your-email"
   EMAIL_PASSWORD="your-email-password"
   EMAIL_HOST="smtp.gmail.com"
   EMAIL_PORT="587"
   EMAIL_FROM="Your Name <your-email>"
   DATABASE_URL="postgresql://user:password@host:port/database"
   ```

## Running the Application

### Option 1: Using the run script
```bash
./run.sh
```

### Option 2: Manual start
```bash
source venv/bin/activate
python main.py
```

The server will start on `http://localhost:8080`

## API Documentation

Once the server is running, you can access:
- **Interactive API docs**: `http://localhost:8080/docs`
- **OpenAPI schema**: `http://localhost:8080/openapi.json`

## Key Endpoints

### Authentication
- `POST /auth/signin` - User signin
- `GET /auth/fetch` - Fetch user data

### Vision Boards
- `GET /v1/visionboard` - Get vision boards with filters
- `POST /v1/visionboard/create` - Create new vision board
- `GET /v1/visionboard/{id}` - Get specific vision board

### Users
- `GET /v1/following/{user_id}` - Get user's following list
- `GET /v1/following/{user_id}/{role}` - Get following users by role
- `PUT /v1/follow/{user_id}` - Follow a user

## Development

The project uses:
- **FastAPI** for the web framework
- **Supabase** for user management and some data
- **PostgreSQL** (via asyncpg) for vision board data
- **Pydantic** for data validation
- **JWT** for authentication

## Project Structure

```
creatist-backend/
├── src/
│   ├── app.py              # FastAPI application setup
│   ├── models/             # Pydantic models
│   ├── routes/             # API route handlers
│   └── utils/              # Utility functions and handlers
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
└── run.sh                  # Quick start script
```

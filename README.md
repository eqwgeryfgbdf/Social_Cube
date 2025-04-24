# Discord Bot Dashboard

A modern web dashboard for managing Discord bots, built with Django and Bootstrap 5.

## Features

- Discord OAuth2 Integration
- Bot Management
- Server Management
- Command Configuration
- Activity Logging
- Plugin System

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/discord-bot-dashboard.git
cd discord-bot-dashboard
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

5. Set up your environment variables in `.env`:
- Generate a Django secret key
- Add your Discord application credentials
- Configure your database settings

6. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

7. Create a superuser:
```bash
python manage.py createsuperuser
```

8. Run the development server:
```bash
python manage.py runserver
```

Visit http://localhost:8000 to access the dashboard.

## Project Structure

```
social_cube/
├── dashboard/           # Main application
│   ├── models.py       # Database models
│   ├── views.py        # View logic
│   ├── urls.py         # URL routing
│   └── templates/      # HTML templates
├── static/             # Static files
├── templates/          # Global templates
├── social_cube/        # Project settings
└── manage.py          # Django management script
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
# Park Up Edge Node - Setup Instructions

## Prerequisites

- Python 3.11 or higher
- Git
- MySQL Server (for user synchronization)
- ESP32 Cam (optional, for camera integration)

## Installation Steps

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd park_up_edge_node
```

### 2. Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt
```

### 4. Environment Configuration
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your configurations:
# - MySQL credentials
# - ESP32 cam IP address
# - Backend URL
```

### 5. Database Setup (Optional - for user sync)
```bash
# If using MySQL user synchronization:
# 1. Create database
# 2. Run database_schema.sql
# 3. Configure MySQL credentials in .env
```

### 6. Run the Application
```bash
# Start the edge node server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Quick Test

### Test ESP32 Camera Integration
```bash
# Run the improved plate reader
python improved_plate_reader.py
```

### Test API Endpoints
```bash
# Use the HTTP test files:
# - test_main.http (basic endpoints)
# - test_esp32_stream.http (ESP32 camera)
# - test_users.http (user synchronization)
```

## Configuration Files

- `.env` - Environment variables
- `requirements.txt` - Python dependencies
- `database_schema.sql` - Database setup
- `pyproject.toml` - Project configuration

## Key Features

1. **License Plate Recognition** - Upload images or use ESP32 cam
2. **ESP32 Camera Integration** - Real-time stream processing
3. **User Synchronization** - MySQL to Java backend sync
4. **Parking Site Management** - Occupancy tracking
5. **Monitoring Analytics** - Data collection

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure virtual environment is activated
2. **OpenCV Issues**: May need additional system libraries
3. **MySQL Connection**: Verify credentials and server status
4. **ESP32 Not Found**: Check IP address and network connectivity

### Dependency Issues

If you encounter issues with specific packages:

```bash
# Update pip
python -m pip install --upgrade pip

# Install packages individually if needed
pip install fastapi uvicorn
pip install opencv-python
pip install fast-alpr
pip install pymysql sqlalchemy
```

## Production Deployment

For production deployment, consider:

1. Use a production WSGI server (e.g., gunicorn)
2. Set up proper logging
3. Configure reverse proxy (nginx)
4. Set up monitoring and health checks
5. Use environment variables for sensitive data

## Support

- Check documentation files in the project
- Review HTTP test files for API examples
- Verify environment configuration

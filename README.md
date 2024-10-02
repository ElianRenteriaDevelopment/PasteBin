
# Flask PasteBin Application

This is a simple PasteBin-like web application built with Flask. The app allows users to paste text or code and share it via a URL. This application is containerized using Docker and served in production with Gunicorn.

## Features

- Paste and share text or code via a simple interface.
- The application runs in a Docker container and can be deployed easily.
- Production-ready with Gunicorn for serving the app in a scalable way.

## Getting Started

### Prerequisites

- Docker installed on your machine.
- Python 3.x and pip if you're running the app locally.

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-repo/pastebin-app.git
   cd pastebin-app
   ```

2. Create a virtual environment and install dependencies (if running locally):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. To run the app in development mode (locally):
   ```bash
   python app.py
   ```

4. To build and run the app with Docker in production mode using Gunicorn:
   ```bash
   docker build -t flask-app .
   docker run -d -p 8118:8118 flask-app
   ```

5. Visit `http://localhost:8118` to access the app.

## Running Tests

No specific tests are provided yet.

## Deployment

The application is containerized using Docker. You can deploy it using any container orchestration platform or directly with Docker.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For any inquiries or support, feel free to contact me at [elianrenteriadevelopment@gmail.com](mailto:elianrenteriadevelopment@gmail.com).

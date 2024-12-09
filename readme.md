# Talent API

Talent is a job marketplace for women developers, connecting them with new opportunities to grow their careers.

## Prerequisites

- **Python** (version 3.x)
- **pip** (Python package installer)
- **Docker** (if running in a Docker container)

## Getting Started

### Steps to Set Up and Run the App

#### Clone the Repository, Set Up a Virtual Environment, Install Dependencies, and Run the App

```bash
# Clone the repository
git clone git@github.com:GirlCodeZA/talentAPI.git
cd talentBackEnd
```
### Using Autamted Script
```bash
make clean  # This will remove the existing virtual environment
make setup # To set up the environment
make up #To start the app locally

#To build and run in Docker:
make docker-build 
make docker-up
```


### Set up a virtual environment
```bash
python3 -m venv venv
```

### Activate the virtual environment (Mac/Linux)
```bash
source venv/bin/activate
```

### Activate the virtual environment (Windows)
```bash
python -m venv venv
venv\Scripts\activate
```

# Install dependencies
```bash
pip install -r requirements.txt
```

### Run the app
```bash
python run.py
```

# Open a browser and go to http://localhost:5000

### Running the App in Docker
    
```bash
# Build the Docker image
docker build -t talent-backend .

# Run the Docker Container
docker run -d -p 8000:8000 talent-backend

#The app should now be accessible at http://localhost:8000. 
# his will run the FastAPI app in a Docker container, mapping port 8000 
# on your machine to the container’s port 8000.
```

```bash
# Run tests
```bash
# Run tests (if any are available in run.py)
python run.py
```

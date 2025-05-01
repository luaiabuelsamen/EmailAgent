# Installation Guide

## Requirements

- Python 3.8 or higher
- pip (Python package installer)

## Installation Steps

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/cognitive-email-ecosystem.git
   cd cognitive-email-ecosystem
   ```

2. Set up a virtual environment (optional but recommended):
   ```
   python -m venv venv
   ```

   Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

3. Install the package and its dependencies:
   ```
   pip install -e .
   ```

4. Run the setup script to ensure all directories are created:
   ```
   python setup.py
   ```

## Running the System

### Observer Agent Demo

Run the observer agent demonstration:
```
python observe_demo.py
```

### Web Interface

Start the web interface to visualize the email processing system:
```
python email_interface.py
```
Then open your browser and navigate to: http://localhost:5000

### Individual Components

You can also run individual components:

1. Ingestion Agent:
   ```
   python src/ingestionAgent.py
   ```

2. Cognitive Email Adapter:
   ```
   python src/cognitive_email_adapter.py
   ```

## Running Tests

Run the test suite:
```
python -m unittest discover tests
``` 
# Final Project: Meal Order Glucose Coach

This project teachers usrs how to use meal order to reduce blood sugar spikes.

## Run

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the app:
   ```bash
   python3 server.py
   ```
3. Open:
   ```
   http://127.0.0.1:5000
   ```

## Route Flow

- Home: `/`
- Learning pages: `/learn/<n>`
- Quiz pages: `/quiz/<n>`
- Quiz results: `/quiz/results`

## Backend Data Tracking

- Page entries, learning selections, and quiz answers are persisted to:
  - `activity_log.json`


# HW10 Technical Prototype: Meal Order Glucose Coach

Flask prototype for the topic: using meal order to reduce blood sugar spikes.

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

## Required HW10 Route Flow

- Home: `/`
- Learning pages: `/learn/<n>`
- Quiz pages: `/quiz/<n>`
- Quiz results: `/quiz/results`

## Backend Data Tracking

- Session state is tracked in-memory for one user at a time.
- Page entries, learning selections, and quiz answers are persisted to:
  - `activity_log.json`
- Interactive predictions, chart toggles, and meal-order rearrangements are also logged as events.
- Structured lesson/quiz content is stored in:
  - `prototype_content.json`

## Interactive Pieces

- Lesson 4 includes a prediction prompt and toggleable glucose-response chart.
- Quiz question 1 is a build-the-order activity for salad, chicken, and rice.
- Quiz hints are hidden until the learner chooses to reveal them.

## Debug Endpoint (for TA demo)

- `GET /api/progress`
- Returns JSON showing stored page entries, learning selections, quiz answers, and event history.

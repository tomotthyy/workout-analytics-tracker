# Workout Analytics Tracker
GitHub Repository Link: https://github.com/tomotthyy/workout-analytics-tracker

## Description
Python-based project which aims to track workout info and determine future growth with plateau detection and other assitance features.

### Purpose
This project was created to improve the understanding of what can be considered an optimal amount of progress in hypertrophy training. The goal is to provide an in-depth analysis of weight and repetitions to give further information on whether or not a user is growing along the expected curve depending on their skill level (Beginner -> Intermediate -> Advanced)

### Features
- Log workouts with exercises, sets, reps, weight, and RIR
- Calculate total training volume per exercise
- Estimate 1RM per exercise
- Detect plateaus and predict expected growth
- CLI interface and FastAPI backend for future web integration

### Example Analytics
- Total tonnage per exercise
- Estimated 1RM per session
- Plateau detection
- Expected growth ranges for beginner, intermediate, and advanced trainees

### Future Improvements (In order of next to be implemented)
- Web frontend for easier use
- User profiles and accounts
- Export graphs and reports

## Setup
This project is currently run locally without a server hosting environment. It includes a FastAPI backend for data and a React frontend loaded in the browser.
### Backend (Python)

1. Make sure you have **Python 3.10+** installed.
2. Install dependencies from the requirements.txt file: `pip install -r requirements.txt`
### Frontend (React)
3. Open the index.html file in your browser
4. Track your workouts and see how your progress is!

## License
MIT License

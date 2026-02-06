from typing import List
from datetime import datetime
import numpy as np

# Function to estimate 1RM using Epley formula
def estimate_1rm(weight: float, reps: int) -> float:
    return weight * (1 + reps / 30)

# Function to get the best estimated 1RM for a specific exercise in a workout
def best_1rm_for_workout(workout_dict: dict, exercise_name: str) -> float | None:
    best = None
    for e in workout_dict["exercises"]:
        if e["name"].lower() == exercise_name.lower():
            for s in e["sets"]:
                est = estimate_1rm(s["weight"], s["reps"])
                if best is None or est > best:
                    best = est
    return best

# Function to get 1RM timeseries for a specific exercise
def get_1rm_timeseries(workouts: List[dict], exercise_name: str):
    series = []
    for w in workouts:
        val = best_1rm_for_workout(w, exercise_name)
        if val:
            dt = datetime.fromisoformat(w["workout_date"])
            series.append((dt, val))
    return sorted(series, key=lambda x: x[0])

# Function to detect plateau in 1RM progression
def detect_plateau(timeseries, min_points=5, slope_threshold=0.01):
    if len(timeseries) < min_points:
        return False, None

    y = np.array([v for _, v in timeseries])
    x = np.arange(len(y))

    slope = np.polyfit(x, y, 1)[0]

    plateau = slope < slope_threshold
    return plateau, slope
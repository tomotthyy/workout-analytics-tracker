import json
from pathlib import Path
from datetime import date
from models import WorkoutEntry, ExerciseEntry, SetEntry

DATA_PATH = Path("data/workouts.json")

# Function to convert WorkoutEntry dataclass to a dictionary
def workout_to_dict(workout: WorkoutEntry) -> dict:
    """Convert a WorkoutEntry dataclass to a dictionary."""
    return {
        "workout_title": workout.workout_title,
        "workout_date": workout.workout_date.strftime("%d, %B, %Y"),
        "workout_time": workout.workout_time,
        "exercises": [
            {
                "exercise_name": exercise.exercise_name,
                "muscle_group": exercise.muscle_group,
                "rest_time": exercise.rest_time,
                "sets": [
                    {
                        "reps": s.reps,
                        "weight": s.weight,
                        "rir": s.rir
                    } for s in exercise.sets
                ]
            } for exercise in workout.exercises
        ],
        "workout_time": workout.workout_time
    }

# Function to save a workout entry to the JSON file
def save_workout(workout: WorkoutEntry):
    DATA_PATH.parent.mkdir(exist_ok=True)

    if DATA_PATH.exists():
        content = DATA_PATH.read_text().strip()
        data = json.loads(content) if content else []
    else:
        data = []
    
    data.append(workout_to_dict(workout))
    DATA_PATH.write_text(json.dumps(data, indent=2))

def load_workouts() -> list[dict]:
    if not DATA_PATH.exists():
        return []
    return json.loads(DATA_PATH.read_text())

def clear_all_workouts():
    """Delete all stored workouts."""
    if DATA_PATH.exists():
        DATA_PATH.unlink()
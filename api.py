from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from datetime import date, datetime
from pydantic import BaseModel
from typing import List, Optional
import numpy as np
from models import WorkoutEntry, ExerciseEntry, SetEntry
from storage import load_workouts, save_workout
from analytics import get_1rm_timeseries_obj, detect_plateau, weekly_volume_by_muscle, estimate_1rm
from pathlib import Path
import json

app = FastAPI(title="Gym Tracker API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Pydantic Models ============
class SetModel(BaseModel):
    reps: int
    weight: float
    rir: Optional[int] = None

class ExerciseModel(BaseModel):
    exercise_name: str
    muscle_group: str
    sets: List[SetModel]
    rest_time: Optional[int] = None

class WorkoutModel(BaseModel):
    workout_title: str
    workout_date: str  # ISO format: YYYY-MM-DD
    exercises: List[ExerciseModel]
    workout_time: Optional[int] = None

class WorkoutResponse(BaseModel):
    workout_title: str
    workout_date: str
    exercises: List[dict]
    workout_time: Optional[int] = None

# ============ Helper Functions ============
def convert_json_to_workout(data: dict) -> WorkoutEntry:
    """Convert JSON/dict to WorkoutEntry object."""
    sets = [SetEntry(reps=s['reps'], weight=s['weight'], rir=s.get('rir')) 
            for s in data['sets']]
    exercise = ExerciseEntry(
        exercise_name=data['exercise_name'],
        muscle_group=data['muscle_group'],
        sets=sets,
        rest_time=data.get('rest_time')
    )
    return exercise

def parse_workout_date(date_str: str) -> date:
    """Parse ISO format date string."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()

# ============ API Routes ============

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Gym Tracker API is running"}

@app.get("/api/workouts")
def get_all_workouts() -> list[dict]:
    """Get all workouts."""
    try:
        return load_workouts()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/workouts")
def create_workout(workout: WorkoutModel):
    """Create a new workout."""
    try:
        # Convert Pydantic model to WorkoutEntry
        workout_date = parse_workout_date(workout.workout_date)
        exercises = []
        
        for ex in workout.exercises:
            sets = [SetEntry(reps=s.reps, weight=s.weight, rir=s.rir) for s in ex.sets]
            exercise = ExerciseEntry(
                exercise_name=ex.exercise_name,
                muscle_group=ex.muscle_group,
                sets=sets,
                rest_time=ex.rest_time
            )
            exercises.append(exercise)
        
        workout_entry = WorkoutEntry(
            workout_title=workout.workout_title,
            workout_date=workout_date,
            exercises=exercises,
            workout_time=workout.workout_time
        )
        
        save_workout(workout_entry)
        return {"status": "success", "message": "Workout saved"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/exercises")
def get_all_exercises() -> list[str]:
    """Get list of unique exercises from all workouts."""
    try:
        workouts = load_workouts()
        exercises = set()
        for w in workouts:
            for ex in w.get('exercises', []):
                exercises.add(ex['exercise_name'])
        return sorted(list(exercises))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/{exercise_name}")
def get_exercise_analytics(exercise_name: str):
    """Get 1RM progression and plateau detection for an exercise."""
    try:
        # Load workouts from JSON
        workouts_data = load_workouts()
        
        # Convert JSON to WorkoutEntry objects
        workouts = []
        for w in workouts_data:
            exercises = []
            for ex in w.get('exercises', []):
                sets = [SetEntry(reps=s['reps'], weight=s['weight'], rir=s.get('rir')) 
                       for s in ex.get('sets', [])]
                exercise = ExerciseEntry(
                    exercise_name=ex['exercise_name'],
                    muscle_group=ex['muscle_group'],
                    sets=sets,
                    rest_time=ex.get('rest_time')
                )
                exercises.append(exercise)
            
            workout = WorkoutEntry(
                workout_title=w['workout_title'],
                workout_date=datetime.strptime(w['workout_date'], "%d, %B, %Y").date(),
                exercises=exercises,
                workout_time=w.get('workout_time')
            )
            workouts.append(workout)
        
        # Get 1RM timeseries
        timeseries = get_1rm_timeseries_obj(workouts, exercise_name)
        
        if not timeseries:
            raise HTTPException(status_code=404, detail="No data found for this exercise")
        
        # Detect plateau
        plateau, slope = detect_plateau(timeseries)
        
        # Format for JSON response
        timeseries_formatted = [
            {"date": d.isoformat(), "oneRM": float(val)}
            for d, val in timeseries
        ]
        
        return {
            "exercise_name": exercise_name,
            "timeseries": timeseries_formatted,
            "plateau_detected": plateau,
            "slope": float(slope) if slope else None,
            "latest_1rm": float(timeseries[-1][1]) if timeseries else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/muscle/{muscle_group}")
def get_muscle_group_stats(muscle_group: str):
    """Get volume and exercise stats for a muscle group."""
    try:
        workouts_data = load_workouts()
        
        # Convert JSON to WorkoutEntry objects
        workouts = []
        for w in workouts_data:
            exercises = []
            for ex in w.get('exercises', []):
                sets = [SetEntry(reps=s['reps'], weight=s['weight'], rir=s.get('rir')) 
                       for s in ex.get('sets', [])]
                exercise = ExerciseEntry(
                    exercise_name=ex['exercise_name'],
                    muscle_group=ex['muscle_group'],
                    sets=sets,
                    rest_time=ex.get('rest_time')
                )
                exercises.append(exercise)
            
            workout = WorkoutEntry(
                workout_title=w['workout_title'],
                workout_date=datetime.strptime(w['workout_date'], "%d, %B, %Y").date(),
                exercises=exercises,
                workout_time=w.get('workout_time')
            )
            workouts.append(workout)
        
        # Get volume by muscle group
        volume_data = weekly_volume_by_muscle(workouts)
        
        return {
            "muscle_group": muscle_group,
            "volume": volume_data.get(muscle_group, 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/summary")
def get_summary_stats():
    """Get overall summary stats."""
    try:
        workouts_data = load_workouts()
        
        if not workouts_data:
            return {
                "total_workouts": 0,
                "total_exercises": 0,
                "total_volume": 0
            }
        
        # Convert to WorkoutEntry objects
        workouts = []
        exercises_set = set()
        total_volume = 0
        
        for w in workouts_data:
            exercises = []
            for ex in w.get('exercises', []):
                exercises_set.add(ex['exercise_name'])
                sets = [SetEntry(reps=s['reps'], weight=s['weight'], rir=s.get('rir')) 
                       for s in ex.get('sets', [])]
                
                # Calculate volume for this exercise
                for s in sets:
                    total_volume += s.weight * s.reps
                
                exercise = ExerciseEntry(
                    exercise_name=ex['exercise_name'],
                    muscle_group=ex['muscle_group'],
                    sets=sets,
                    rest_time=ex.get('rest_time')
                )
                exercises.append(exercise)
            
            workout = WorkoutEntry(
                workout_title=w['workout_title'],
                workout_date=datetime.strptime(w['workout_date'], "%d, %B, %Y").date(),
                exercises=exercises,
                workout_time=w.get('workout_time')
            )
            workouts.append(workout)
        
        return {
            "total_workouts": len(workouts_data),
            "unique_exercises": len(exercises_set),
            "total_volume": total_volume
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


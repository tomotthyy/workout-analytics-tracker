from dataclasses import dataclass
from datetime import date
from typing import List, Optional

# Dataclass for entering set information
@dataclass
class SetEntry:
    reps: int # number of repetitions
    weight: float  # weight in kilograms
    rir: Optional[int] = None  # reps in reserve, optional field

# Dataclass for entering exercise information
@dataclass
class ExerciseEntry:
    exercise_name: str # name of the exercise
    muscle_group: str # targeted muscle group
    sets: List[SetEntry]  # list of sets done
    rest_time: Optional[int] = None  # rest time in minutes, optional field

# Dataclass for entering workout information
@dataclass
class WorkoutEntry:
    workout_title: str  # title of the workout (e.g., "Push day")
    workout_date: date  # date of the workout
    exercises: List[ExerciseEntry]  # list of exercises done
    workout_time: Optional[int] = None  # total workout time in minutes, optional field
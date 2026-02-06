#!/usr/bin/env python3
"""
CLI interface for entering and viewing workout data.
"""

from datetime import datetime, date
from models import WorkoutEntry, ExerciseEntry, SetEntry
from storage import save_workout, load_workouts, clear_all_workouts
from collections import defaultdict
import json
import numpy as np


def parse_date(date_str: str) -> date:
    """Parse date string in format DD/MM/YYYY or use today's date."""
    if not date_str.strip():
        return date.today()
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    except ValueError:
        print("Invalid date format. Using today's date.")
        return date.today()

# Display muscle group selection
def get_muscle_group() -> str:
    """Prompt user to select or enter a muscle group."""
    common_groups = ["Chest", "Back", "Shoulders", "Legs", "Arms", "Core"]
    
    print("\nCommon muscle groups:")
    for i, group in enumerate(common_groups, 1):
        print(f"  {i}. {group}")
    print(f"  {len(common_groups) + 1}. Custom")
    
    choice = input("Select muscle group (number or custom name): ").strip()
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(common_groups):
            return common_groups[idx]
    except ValueError:
        pass
    
    return choice if choice else "General"

# Input multiple sets for an exercise
def input_sets() -> list[SetEntry]:
    """Input multiple sets for an exercise."""
    sets = []
    print(f"\n  Enter sets (press Enter with empty weight to finish):")
    
    set_num = 1
    while True:
        weight_input = input(f"    Set {set_num} - Weight (kg): ").strip()
        if not weight_input:
            break
        
        try:
            weight = float(weight_input)
            reps = int(input(f"    Set {set_num} - Reps: ").strip())
            rir_input = input(f"    Set {set_num} - Reps in Reserve (optional): ").strip()
            rir = int(rir_input) if rir_input else None
            
            sets.append(SetEntry(reps=reps, weight=weight, rir=rir))
            set_num += 1
        except ValueError:
            print("    Invalid input. Please enter numbers.")
    
    return sets

# Input a single exercise
def input_exercise() -> ExerciseEntry:
    """Input a single exercise with all its sets."""
    print("\n--- New Exercise ---")
    exercise_name = input("Exercise name: ").strip()
    muscle_group = get_muscle_group()
    
    sets = input_sets()
    
    if not sets:
        print("No sets entered. Skipping exercise.")
        return None
    
    rest_time_input = input(f"Rest time between sets (minutes, optional): ").strip()
    rest_time = int(rest_time_input) if rest_time_input else None
    
    return ExerciseEntry(
        exercise_name=exercise_name,
        muscle_group=muscle_group,
        sets=sets,
        rest_time=rest_time
    )

# Input a complete workout
def input_workout() -> WorkoutEntry:
    """Input a complete workout with multiple exercises."""
    print("\n" + "="*50)
    print("NEW WORKOUT ENTRY")
    print("="*50)
    
    workout_title = input("Workout title (e.g., 'Push Day'): ").strip()
    date_input = input("Workout date (DD/MM/YYYY or press Enter for today): ").strip()
    workout_date = parse_date(date_input)
    
    exercises = []
    while True:
        exercise = input_exercise()
        if exercise:
            exercises.append(exercise)
        
        if not input("\nAdd another exercise? (y/n): ").strip().lower().startswith('y'):
            break
    
    if not exercises:
        print("No exercises entered. Workout not saved.")
        return None
    
    workout_time_input = input("Total workout time (minutes, optional): ").strip()
    workout_time = int(workout_time_input) if workout_time_input else None
    
    return WorkoutEntry(
        workout_title=workout_title,
        workout_date=workout_date,
        exercises=exercises,
        workout_time=workout_time
    )

# Display a single workout
def display_workout(workout_dict: dict):
    """Display a workout entry in a readable format."""
    print(f"\n {workout_dict['workout_title']} - {workout_dict['workout_date']}")
    if workout_dict.get('workout_time'):
        print(f"   Duration: {workout_dict['workout_time']} minutes")
    
    for exercise in workout_dict['exercises']:
        print(f"   • {exercise['exercise_name']} ({exercise['muscle_group']})")
        for i, s in enumerate(exercise['sets'], 1):
            rir_str = f" | {s['rir']} RIR" if s.get('rir') is not None else ""
            print(f"     Set {i}: {s['weight']}kg × {s['reps']}{rir_str}")

# Display all saved workouts
def view_workouts():
    """Display all saved workouts."""
    workouts = load_workouts()
    
    if not workouts:
        print("\nNo workouts saved yet.")
        return
    
    print(f"\n{'='*50}")
    print(f"WORKOUT HISTORY ({len(workouts)} workouts)")
    print(f"{'='*50}")
    
    for i, workout in enumerate(workouts, 1):
        display_workout(workout)
    
    print()


def estimate_1rm(weight: float, reps: int) -> float:
    """Estimate 1RM using Epley formula."""
    return weight * (1 + reps / 30)

# Advanced Analytics Functions
def detect_plateau_and_growth(one_rm_timeseries):
    """
    Detect plateau in 1RM progression and estimate growth in one month.
    Returns: (is_plateau, growth_estimate)
    """
    if len(one_rm_timeseries) < 3:
        return False, 0.0
    
    # Sort by date
    sorted_series = sorted(one_rm_timeseries, key=lambda x: x[0])
    
    # Extract values
    y = np.array([v for _, v in sorted_series])
    x = np.arange(len(y))
    
    # Fit linear trend
    slope, intercept = np.polyfit(x, y, 1)
    
    # Detect plateau (slope near zero)
    is_plateau = abs(slope) < 0.01
    
    # Estimate growth per day based on slope
    # slope is per workout session, estimate ~4 workouts per month (30 days)
    growth_per_month = slope * 4
    
    return is_plateau, growth_per_month


def view_performance_by_muscle():
    """Display performance metrics grouped by muscle group."""
    workouts = load_workouts()
    
    if not workouts:
        print("\nNo workouts saved yet.")
        return
    
    # Aggregate data by muscle group
    muscle_data = defaultdict(lambda: {
        'exercises': defaultdict(list),
        'total_volume': 0,
        'max_1rm': 0,
        'one_rm_timeseries': [],  # Track (date, 1RM) tuples
    })
    
    for workout in workouts:
        # Parse date
        date_str = workout['workout_date']
        try:
            workout_date = datetime.strptime(date_str, "%d, %B, %Y").date()
        except ValueError:
            continue
        
        for exercise in workout['exercises']:
            muscle = exercise['muscle_group']
            exercise_name = exercise['exercise_name']
            
            # Track best 1RM for this exercise in this workout
            best_1rm_workout = 0
            
            for s in exercise['sets']:
                weight = s['weight']
                reps = s['reps']
                volume = weight * reps
                
                # Track volume
                muscle_data[muscle]['total_volume'] += volume
                
                # Track 1RM per exercise
                one_rm = estimate_1rm(weight, reps)
                muscle_data[muscle]['exercises'][exercise_name].append(one_rm)
                
                # Track max 1RM
                if one_rm > muscle_data[muscle]['max_1rm']:
                    muscle_data[muscle]['max_1rm'] = one_rm
                
                # Track best 1RM in this workout
                if one_rm > best_1rm_workout:
                    best_1rm_workout = one_rm
            
            # Add to timeseries
            if best_1rm_workout > 0:
                muscle_data[muscle]['one_rm_timeseries'].append((workout_date, best_1rm_workout))
    
    # Display results
    print(f"\n{'='*70}")
    print("PERFORMANCE BY MUSCLE GROUP")
    print(f"{'='*70}")
    
    for muscle in sorted(muscle_data.keys()):
        data = muscle_data[muscle]
        print(f"\n{muscle}")
        print(f"  Total Volume: {data['total_volume']:.0f} kg")
        print(f"  Max Estimated 1RM: {data['max_1rm']:.1f} kg")
        
        # Plateau detection and growth estimate
        is_plateau, growth = detect_plateau_and_growth(data['one_rm_timeseries'])
        plateau_status = "Yes" if is_plateau else "No"
        print(f"  Plateau: {plateau_status}")
        print(f"  Estimated Growth (1 month): {growth:+.1f} kg")
        
        print(f"  Exercises ({len(data['exercises'])}): ", end='')
        
        exercises_list = []
        for exc_name, one_rms in data['exercises'].items():
            avg_1rm = sum(one_rms) / len(one_rms)
            exercises_list.append(f"{exc_name} ({avg_1rm:.0f}kg)")
        
        print(", ".join(exercises_list))
    
    print()




def main_menu():
    """Display main menu and handle user choices."""
    while True:
        print("\n" + "="*50)
        print("GYM TRACKER - Main Menu")
        print("="*50)
        print("1. Add new workout")
        print("2. View all workouts")
        print("3. View performance by muscle group")
        print("4. Clear all workouts")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            workout = input_workout()
            if workout:
                save_workout(workout)
                print("\n✓ Workout saved successfully!")
        
        elif choice == "2":
            view_workouts()
        
        elif choice == "3":
            view_performance_by_muscle()
        
        elif choice == "4":
            confirm = input("⚠️  Are you sure you want to delete ALL workouts? (y/n): ").strip().lower()
            if confirm == "y":
                clear_all_workouts()
                print("✓ All workouts cleared!")
            else:
                print("Cancelled.")
        
        elif choice == "5":
            print("Goodbye!")
            break
        
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    main_menu()

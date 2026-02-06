# Function to classify training level based on months of training
def classify_training_level(months_training: int) -> str:
    if months_training < 6:
        return "beginner"
    elif months_training < 24:
        return "intermediate"
    else:
        return "advanced"

EXPECTED_MONTHLY_GROWTH = {
    "beginner": (0.02, 0.04),
    "intermediate": (0.005, 0.015),
    "advanced": (0.0, 0.005),
}

# Function to get expected growth range based on training level
def expected_growth_range(level: str):
    return EXPECTED_MONTHLY_GROWTH[level]
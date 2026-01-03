import random
from django.utils.text import slugify


def generate_unique_username(first_name, last_name, middle_name=None):
    """
    Generate a unique username based on user's name and random number.
    Format: firstname_lastname_randomnumber (e.g., john_doe_1234)
    
    Args:
        first_name: User's first name
        last_name: User's last name
        middle_name: User's middle name (optional)
    
    Returns:
        A unique username string
    """
    from .models import User
    
    # Clean and prepare name parts
    first = slugify(first_name.lower()) if first_name else 'user'
    last = slugify(last_name.lower()) if last_name else 'user'
    
    # Create base username
    if middle_name:
        middle = slugify(middle_name.lower())
        base_username = f"{first}_{middle}_{last}"
    else:
        base_username = f"{first}_{last}"
    
    # Ensure base username is not too long (Django username max is 150)
    if len(base_username) > 120:
        base_username = base_username[:120]
    
    # Try to find a unique username
    max_attempts = 1000
    for attempt in range(max_attempts):
        # Generate random number (4-6 digits)
        random_num = random.randint(1000, 999999)
        username = f"{base_username}_{random_num}"
        
        # Check if username already exists
        if not User.objects.filter(username=username).exists():
            return username
    
    # If we couldn't find a unique username after max attempts,
    # use timestamp-based approach
    import time
    timestamp = int(time.time())
    username = f"{base_username}_{timestamp}"
    
    # Final check and add more randomness if needed
    counter = 0
    while User.objects.filter(username=username).exists() and counter < 100:
        username = f"{base_username}_{timestamp}_{counter}"
        counter += 1
    
    return username


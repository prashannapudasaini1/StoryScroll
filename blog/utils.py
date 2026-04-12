import random
import re
import math
from collections import Counter
from django.utils.text import slugify


# Common English stop words
STOP_WORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
    'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
    'to', 'was', 'will', 'with', 'the', 'this', 'but', 'they', 'have',
    'had', 'what', 'said', 'each', 'which', 'their', 'time', 'if',
    'up', 'out', 'many', 'then', 'them', 'these', 'so', 'some', 'her',
    'would', 'make', 'like', 'into', 'him', 'has', 'two', 'more',
    'very', 'after', 'words', 'long', 'than', 'first', 'been', 'call',
    'who', 'oil', 'sit', 'now', 'find', 'down', 'day', 'did', 'get',
    'come', 'made', 'may', 'part'
}


def preprocess_text(text):
    """
    Preprocess text: lowercase, tokenize, and remove stop words.
    
    Args:
        text: Input text string
    
    Returns:
        List of processed tokens
    """
    if not text:
        return []
    
    # Convert to lowercase and tokenize (split on non-word characters)
    tokens = re.findall(r'\b\w+\b', text.lower())
    
    # Remove stop words and short words (less than 2 characters)
    tokens = [token for token in tokens if token not in STOP_WORDS and len(token) > 2]
    
    return tokens


def create_frequency_vector(tokens):
    """
    Create a frequency vector (Counter) from tokens.
    
    Args:
        tokens: List of tokens
    
    Returns:
        Counter object with token frequencies
    """
    return Counter(tokens)


def get_all_words(posts):
    """
    Get all unique words from a list of posts.
    
    Args:
        posts: QuerySet or list of Post objects
    
    Returns:
        Set of all unique words
    """
    all_words = set()
    for post in posts:
        title_tokens = preprocess_text(post.title)
        content_tokens = preprocess_text(post.content)
        all_words.update(title_tokens)
        all_words.update(content_tokens)
    return all_words


def create_post_vector(post, all_words, title_weight=2.0):
    """
    Create a frequency vector for a post with weighted title.
    
    Args:
        post: Post object
        all_words: Set of all unique words across all posts
        title_weight: Weight multiplier for title words (default: 2.0)
    
    Returns:
        List representing the vector (ordered by all_words)
    """
    # Process title and content separately
    title_tokens = preprocess_text(post.title)
    content_tokens = preprocess_text(post.content)
    
    # Create frequency vectors
    title_vector = create_frequency_vector(title_tokens)
    content_vector = create_frequency_vector(content_tokens)
    
    # Combine with title weighted higher
    combined_vector = Counter()
    for word, count in title_vector.items():
        combined_vector[word] += count * title_weight
    for word, count in content_vector.items():
        combined_vector[word] += count
    
    # Create ordered vector matching all_words
    vector = [combined_vector.get(word, 0) for word in sorted(all_words)]
    return vector


def cosine_similarity(vec1, vec2):
    """
    Calculate cosine similarity between two vectors.
    
    Formula: Similarity = (A . B) / (||A|| * ||B||)
    
    Args:
        vec1: First vector (list of numbers)
        vec2: Second vector (list of numbers)
    
    Returns:
        Cosine similarity score (0 to 1)
    """
    if len(vec1) != len(vec2):
        return 0.0
    
    # Calculate dot product
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # Calculate magnitudes
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    
    # Avoid division by zero
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    # Calculate cosine similarity
    similarity = dot_product / (magnitude1 * magnitude2)
    return similarity


def get_post_weighted_counter(post, title_weight=2.0):
    """Token counts for title (weighted) plus content, after stop-word removal."""
    title_tokens = preprocess_text(post.title)
    content_tokens = preprocess_text(post.content)
    title_vector = create_frequency_vector(title_tokens)
    content_vector = create_frequency_vector(content_tokens)
    combined = Counter()
    for word, count in title_vector.items():
        combined[word] += count * title_weight
    for word, count in content_vector.items():
        combined[word] += count
    return combined


def shared_terms_between_posts(counter_a, counter_b, limit=12):
    """Terms present in both weighted counters, ordered by overlap strength."""
    common = set(counter_a) & set(counter_b)
    if not common:
        return []

    def overlap_score(word):
        return min(counter_a[word], counter_b[word])

    ordered = sorted(common, key=overlap_score, reverse=True)
    return ordered[:limit]


def get_recommended_posts_with_details(current_post, num_recommendations=5):
    """
    Recommend posts by cosine similarity on weighted title+content vectors.

    Returns:
        list[dict]: Each item has keys: post, similarity (0..1), shared_terms (list[str]),
        same_category (bool), explanation (short human-readable line).
    """
    from .models import Post

    all_posts = Post.objects.exclude(id=current_post.id)
    if not all_posts.exists():
        return []

    all_posts_with_current = Post.objects.filter(
        id__in=[current_post.id] + list(all_posts.values_list('id', flat=True))
    )
    all_words = get_all_words(all_posts_with_current)
    if not all_words:
        return []

    current_vector = create_post_vector(current_post, all_words)
    current_counter = get_post_weighted_counter(current_post)

    scored = []
    for candidate in all_posts:
        post_vector = create_post_vector(candidate, all_words)
        similarity = cosine_similarity(current_vector, post_vector)
        if similarity <= 0:
            continue
        other_counter = get_post_weighted_counter(candidate)
        shared_terms = shared_terms_between_posts(current_counter, other_counter, 14)
        same_category = candidate.category == current_post.category
        pct = similarity * 100.0
        if shared_terms:
            preview = ', '.join(shared_terms[:5])
            if len(shared_terms) > 5:
                preview += ', …'
            term_part = f'Overlapping words include: {preview}.'
        else:
            term_part = 'Overlap is from weighted term combinations rather than a short shared word list.'
        cat_part = 'Same category as this post.' if same_category else 'Different category; match is from shared wording.'
        explanation = (
            f'Score {pct:.1f}%. {cat_part} {term_part}'
        )
        scored.append({
            'post': candidate,
            'similarity': similarity,
            'shared_terms': shared_terms,
            'same_category': same_category,
            'explanation': explanation,
        })

    scored.sort(key=lambda x: x['similarity'], reverse=True)
    return scored[:num_recommendations]


def get_recommended_posts(current_post, num_recommendations=5):
    """
    Get recommended posts based on content similarity using cosine similarity.

    Returns:
        List of Post objects sorted by similarity (most similar first)
    """
    details = get_recommended_posts_with_details(current_post, num_recommendations)
    return [item['post'] for item in details]


def recommendation_payload_for_cache(current_post, num_recommendations=5):
    """
    Build a pickle-friendly list for cache: post ids plus explanation fields.
    """
    details = get_recommended_posts_with_details(current_post, num_recommendations)
    return [
        {
            'post_id': item['post'].id,
            'similarity': item['similarity'],
            'shared_terms': item['shared_terms'],
            'same_category': item['same_category'],
            'explanation': item['explanation'],
        }
        for item in details
    ]


def materialize_recommendations_from_cache(cached_rows):
    """Turn cached dict rows back into ORM posts plus explanation metadata."""
    from .models import Post

    if not cached_rows:
        return []
    ids = [row['post_id'] for row in cached_rows]
    posts_by_id = {p.id: p for p in Post.objects.filter(id__in=ids)}
    out = []
    for row in cached_rows:
        post = posts_by_id.get(row['post_id'])
        if not post:
            continue
        out.append({
            'post': post,
            'similarity': row['similarity'],
            'shared_terms': row['shared_terms'],
            'same_category': row['same_category'],
            'explanation': row['explanation'],
        })
    return out


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


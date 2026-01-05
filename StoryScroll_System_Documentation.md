# StoryScroll System Documentation

## Table of Contents
1. [Overview](#overview)
2. [Content-Based Recommendation System](#content-based-recommendation-system)
3. [Post Restoration Request System](#post-restoration-request-system)
4. [System Architecture](#system-architecture)
5. [Key Functions and Algorithms](#key-functions-and-algorithms)

---

## Overview

StoryScroll is a Django-based blogging platform that allows Writers to create and manage blog posts, Readers to read and interact with content, and Admins to oversee the entire system. The platform includes advanced features such as:

- **Content-Based Recommendation System**: Uses cosine similarity to recommend similar posts
- **Post Restoration Request System**: Allows writers to request restoration of deleted posts
- **Role-Based Access Control**: Admin, Writer, and Reader roles with different permissions
- **Soft Delete System**: Posts, users, and categories can be soft-deleted and restored

---

## Content-Based Recommendation System

### Overview

The Content-Based Recommendation System uses **Cosine Similarity** to find and recommend posts that are similar to the post a user is currently viewing. This system analyzes the textual content (title and body) of posts to determine similarity.

### Algorithm: Cosine Similarity

Cosine Similarity measures the cosine of the angle between two vectors in a multi-dimensional space. In this context, each post is represented as a vector where each dimension corresponds to a unique word, and the value represents the frequency (weight) of that word in the post.

#### Mathematical Formula

```
Similarity = (A · B) / (||A|| × ||B||)
```

Where:
- **A · B** = Dot product of vectors A and B
- **||A||** = Magnitude (Euclidean norm) of vector A
- **||B||** = Magnitude (Euclidean norm) of vector B

The result is a value between **0 and 1**, where:
- **1** = Identical content
- **0** = Completely different content

### Implementation Details

#### 1. Text Preprocessing

**Function**: `preprocess_text(text)`

**Purpose**: Cleans and normalizes text before analysis

**Steps**:
1. Convert text to lowercase
2. Tokenize using regex pattern `\b\w+\b` (extracts words)
3. Remove stop words (common English words like "the", "a", "is", etc.)
4. Filter out words shorter than 2 characters

**Stop Words List**: Contains 50+ common English stop words including:
- Articles: a, an, the
- Pronouns: he, she, it, they
- Prepositions: in, on, at, by, for
- Common verbs: is, are, was, were, be, been

#### 2. Frequency Vector Creation

**Function**: `create_frequency_vector(tokens)`

**Purpose**: Creates a frequency counter from processed tokens

**Process**:
- Uses Python's `Counter` class to count word occurrences
- Returns a dictionary-like object with word frequencies

#### 3. Weighted Vector Creation

**Function**: `create_post_vector(post, all_words, title_weight=2.0)`

**Purpose**: Creates a numerical vector representing a post with weighted title

**Key Features**:
- **Title Weighting**: Title words are weighted **2x higher** than content words
- **Rationale**: Titles are more descriptive and important for matching
- **Vector Structure**: Creates a fixed-length vector matching all unique words across all posts

**Example**:
```
If a word appears:
- 3 times in title → weight = 3 × 2.0 = 6.0
- 5 times in content → weight = 5 × 1.0 = 5.0
Total weight for that word = 11.0
```

#### 4. Cosine Similarity Calculation

**Function**: `cosine_similarity(vec1, vec2)`

**Purpose**: Calculates the cosine similarity between two post vectors

**Algorithm Steps**:
1. Calculate dot product: `sum(a × b for a, b in zip(vec1, vec2))`
2. Calculate magnitude of vec1: `sqrt(sum(a² for a in vec1))`
3. Calculate magnitude of vec2: `sqrt(sum(b² for b in vec2))`
4. Compute similarity: `dot_product / (magnitude1 × magnitude2)`
5. Handle edge cases (zero vectors, division by zero)

#### 5. Recommendation Generation

**Function**: `get_recommended_posts(current_post, num_recommendations=5)`

**Purpose**: Main function that returns top N similar posts

**Process Flow**:
1. **Get All Posts**: Retrieve all posts except the current one
2. **Build Vocabulary**: Collect all unique words from all posts (including current)
3. **Create Current Post Vector**: Generate vector for the post being viewed
4. **Calculate Similarities**: For each other post:
   - Create its vector
   - Calculate cosine similarity with current post
   - Store (post, similarity_score) pair
5. **Sort and Filter**: 
   - Sort by similarity (descending)
   - Return top 5 posts with similarity > 0

### Caching Strategy

**Cache Duration**: 24 hours (86,400 seconds)

**Cache Key Format**: `recommended_posts_{post_id}`

**Benefits**:
- Reduces computational load
- Improves page load times
- Recommendations remain consistent for 24 hours
- Cache automatically expires and refreshes

**Implementation**:
```python
cache_key = f'recommended_posts_{post_id}'
recommended_posts = cache.get(cache_key)
if recommended_posts is None:
    recommended_posts = get_recommended_posts(post, num_recommendations=5)
    cache.set(cache_key, recommended_posts, 86400)
```

### Example Scenario

**Current Post**:
- Title: "Introduction to Machine Learning"
- Content: "Machine learning is a subset of artificial intelligence..."

**Recommended Posts** (Top 5):
1. "Deep Learning Fundamentals" (Similarity: 0.85)
2. "AI and Neural Networks" (Similarity: 0.72)
3. "Data Science Basics" (Similarity: 0.68)
4. "Python for ML" (Similarity: 0.61)
5. "Statistics for Data Analysis" (Similarity: 0.55)

---

## Post Restoration Request System

### Overview

The Post Restoration Request System allows Writers to request that Admins restore their deleted posts. This provides a controlled workflow for content recovery.

### System Flow

#### 1. Post Deletion
- Writer deletes a post (soft delete)
- Post is marked as `is_deleted = True`
- Post is removed from active listings
- Post data is preserved in database

#### 2. Restoration Request
- Writer views deleted posts in dashboard
- Writer clicks "Request Restore" button
- Writer can optionally add a message explaining why restoration is needed
- System creates a `RestoreRequest` record with status "Pending"

#### 3. Admin Review
- Admin sees pending restore requests in dashboard
- Admin can view:
  - Post title
  - Writer username
  - Request message
  - Request timestamp
- Admin can:
  - **Approve**: Restores the post immediately
  - **Reject**: Denies the restoration request

#### 4. Request Processing

**Approval Process**:
1. Admin clicks "Approve"
2. System sets `post.is_deleted = False`
3. System clears `post.deleted_at = None`
4. System updates `RestoreRequest`:
   - Status → "Approved"
   - `reviewed_at` → Current timestamp
   - `reviewed_by` → Admin user
5. Post becomes visible again

**Rejection Process**:
1. Admin clicks "Reject"
2. System updates `RestoreRequest`:
   - Status → "Rejected"
   - `reviewed_at` → Current timestamp
   - `reviewed_by` → Admin user
3. Post remains deleted
4. Writer can submit a new request if needed

### Database Model

**RestoreRequest Model**:
```python
class RestoreRequest(models.Model):
    post = ForeignKey(Post)           # The post to restore
    writer = ForeignKey(User)         # Writer requesting restoration
    message = TextField(optional)      # Optional explanation
    status = CharField                 # Pending/Approved/Rejected
    created_at = DateTimeField         # Request timestamp
    reviewed_at = DateTimeField        # Review timestamp (optional)
    reviewed_by = ForeignKey(User)     # Admin who reviewed (optional)
```

**Status Values**:
- `Pending`: Awaiting admin review
- `Approved`: Request approved, post restored
- `Rejected`: Request denied, post remains deleted

### User Interface

#### Writer Dashboard
- **Deleted Posts Section**: Shows all deleted posts
- **Request Button**: Opens modal to submit restore request
- **Status Indicator**: Shows "Request Pending" if request already submitted
- **Modal Form**: Allows writer to add optional message

#### Admin Dashboard
- **Restore Requests Section**: Lists all pending requests
- **Request Details**: Shows post title, writer, message, timestamp
- **Action Buttons**: Approve/Reject buttons for each request
- **Badge Counter**: Shows number of pending requests in header

### Business Rules

1. **One Pending Request Per Post**: Writers cannot submit multiple pending requests for the same post
2. **Writer-Only Requests**: Only the original post author can request restoration
3. **Admin-Only Approval**: Only Admin users can approve/reject requests
4. **Soft Delete Requirement**: Only soft-deleted posts can be restored
5. **Request History**: All requests are preserved for audit purposes

---

## System Architecture

### Technology Stack

- **Backend**: Django 4.2+ (Python web framework)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Caching**: Django Local Memory Cache (development) / Redis/Memcached (production)
- **Frontend**: Bootstrap 5, HTML5, JavaScript
- **Authentication**: Django's built-in authentication system

### Project Structure

```
StoryScroll/
├── blog/                    # Main application
│   ├── models.py           # Database models
│   ├── views.py            # View functions
│   ├── utils.py            # Utility functions (recommendation algorithm)
│   ├── urls.py             # URL routing
│   ├── forms.py            # Form definitions
│   ├── decorators.py       # Custom decorators
│   └── templates/          # HTML templates
├── storyscroll/            # Project settings
│   ├── settings.py         # Django settings
│   ├── urls.py             # Root URL configuration
│   └── wsgi.py             # WSGI configuration
└── manage.py               # Django management script
```

### Key Models

1. **User**: Custom user model with roles (Admin, Writer, Reader)
2. **Post**: Blog posts with title, content, category, author
3. **Comment**: Comments on posts with reply support
4. **Like**: Post likes (many-to-many relationship)
5. **Follow**: Writer following system
6. **Category**: Post categories
7. **RestoreRequest**: Post restoration requests

### Role-Based Access Control

#### Admin
- Full system access
- User management
- Post management
- Category management
- Approve/reject writer requests
- Approve/reject restore requests
- Restore deleted items

#### Writer
- Create, edit, delete own posts
- View own post comments
- Reply to comments
- Request post restoration
- View deleted posts
- Read other posts (like Reader)

#### Reader
- Read all posts
- Like posts
- Comment on posts
- Follow writers
- View author rankings

---

## Key Functions and Algorithms

### Recommendation System Functions

#### `preprocess_text(text)`
- **Input**: Raw text string
- **Output**: List of processed tokens
- **Purpose**: Clean and normalize text for analysis

#### `create_frequency_vector(tokens)`
- **Input**: List of tokens
- **Output**: Counter object (word frequencies)
- **Purpose**: Count word occurrences

#### `get_all_words(posts)`
- **Input**: QuerySet of Post objects
- **Output**: Set of unique words
- **Purpose**: Build vocabulary from all posts

#### `create_post_vector(post, all_words, title_weight=2.0)`
- **Input**: Post object, word set, title weight
- **Output**: List of numbers (vector)
- **Purpose**: Create numerical representation of post

#### `cosine_similarity(vec1, vec2)`
- **Input**: Two numerical vectors
- **Output**: Float (0.0 to 1.0)
- **Purpose**: Calculate similarity score

#### `get_recommended_posts(current_post, num_recommendations=5)`
- **Input**: Post object, number of recommendations
- **Output**: List of Post objects
- **Purpose**: Main recommendation function

### Restoration System Functions

#### `request_restore_post(request, post_id)`
- **Purpose**: Writer submits restoration request
- **Validations**: 
  - Post must be deleted
  - Post must belong to writer
  - No existing pending request
- **Creates**: RestoreRequest record

#### `approve_restore_request(request, request_id)`
- **Purpose**: Admin approves and restores post
- **Actions**:
  - Restores post (sets is_deleted=False)
  - Updates RestoreRequest status
  - Records review timestamp and admin

#### `reject_restore_request(request, request_id)`
- **Purpose**: Admin rejects restoration request
- **Actions**:
  - Updates RestoreRequest status
  - Records review timestamp and admin
  - Post remains deleted

### Performance Considerations

#### Recommendation System
- **Time Complexity**: O(n × m) where n = number of posts, m = vocabulary size
- **Optimization**: Caching reduces computation by 99%+ for repeated views
- **Scalability**: For large datasets, consider:
  - Background task processing
  - Database indexing
  - Vector database (e.g., Pinecone, Weaviate)
  - Pre-computed similarity matrix

#### Restoration System
- **Time Complexity**: O(1) for request creation and processing
- **Database Queries**: Minimal (1-2 queries per operation)
- **Scalability**: No performance concerns for typical usage

---

## Usage Examples

### For Writers

1. **View Deleted Posts**:
   - Navigate to Writer Dashboard
   - Scroll to "Deleted Posts" section
   - View all your deleted posts

2. **Request Restoration**:
   - Click "Request Restore" on a deleted post
   - Optionally add a message
   - Submit request
   - Wait for admin approval

3. **Check Request Status**:
   - View "Request Pending" badge if request is pending
   - Check admin dashboard for approval/rejection

### For Admins

1. **View Restore Requests**:
   - Navigate to Admin Dashboard
   - Find "Pending Restore Requests" section
   - Review request details

2. **Approve Request**:
   - Click "Approve" button
   - Post is immediately restored
   - Writer is notified (via system message)

3. **Reject Request**:
   - Click "Reject" button
   - Confirm rejection
   - Post remains deleted
   - Writer can submit new request

### For Readers

1. **View Recommendations**:
   - Open any post detail page
   - Scroll to "Recommended Posts" section
   - Click on recommended posts to read

2. **Recommendation Quality**:
   - Recommendations are based on content similarity
   - Top 5 most similar posts are shown
   - Recommendations update every 24 hours

---

## Future Enhancements

### Recommendation System
1. **Collaborative Filtering**: Add user-based recommendations
2. **Hybrid Approach**: Combine content-based and collaborative filtering
3. **Machine Learning**: Use ML models for better recommendations
4. **Real-time Updates**: Update recommendations when posts are created/edited
5. **User Preferences**: Consider user reading history and preferences

### Restoration System
1. **Auto-Approval**: Auto-approve requests from trusted writers
2. **Bulk Restoration**: Allow restoring multiple posts at once
3. **Request History**: Show all past requests (approved/rejected)
4. **Email Notifications**: Notify writers when requests are processed
5. **Time Limits**: Auto-reject requests older than X days

---

## Conclusion

The StoryScroll platform provides a comprehensive blogging experience with intelligent content recommendations and a robust content management system. The cosine similarity-based recommendation system helps readers discover relevant content, while the restoration request system ensures proper content governance and recovery workflows.

Both systems are designed with performance, scalability, and user experience in mind, using caching strategies and efficient algorithms to provide fast and accurate results.

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Author**: StoryScroll Development Team

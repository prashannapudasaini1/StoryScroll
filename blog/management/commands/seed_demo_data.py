"""
Populate the database with demo users, 100+ posts, random images, likes, and follows.

Usage:
  python manage.py seed_demo_data
  python manage.py seed_demo_data --posts 150

Writes:
  user.txt at the project root (username | email | password | role | full_name)
"""

import io
import random
import secrets
import string
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image

from blog.models import Category, Follow, Like, Post, User

DEFAULT_POST_COUNT = 120
NUM_WRITERS = 28
NUM_READERS = 42
NUM_LIKE_ACTIONS = 450
NUM_FOLLOW_ACTIONS = 180

# Common given names and surnames for realistic demo profiles (fictional combinations)
FIRST_NAMES = [
    'James', 'Mary', 'Robert', 'Patricia', 'John', 'Jennifer', 'Michael', 'Linda',
    'David', 'Elizabeth', 'William', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica',
    'Thomas', 'Sarah', 'Christopher', 'Karen', 'Charles', 'Lisa', 'Daniel', 'Nancy',
    'Matthew', 'Betty', 'Anthony', 'Margaret', 'Mark', 'Sandra', 'Donald', 'Ashley',
    'Steven', 'Kimberly', 'Paul', 'Emily', 'Andrew', 'Donna', 'Joshua', 'Michelle',
    'Kenneth', 'Carol', 'Kevin', 'Amanda', 'Brian', 'Dorothy', 'George', 'Melissa',
    'Timothy', 'Deborah', 'Ronald', 'Stephanie', 'Jason', 'Rebecca', 'Edward', 'Sharon',
    'Jeffrey', 'Laura', 'Ryan', 'Cynthia', 'Jacob', 'Kathleen', 'Gary', 'Amy',
    'Nicholas', 'Angela', 'Eric', 'Shirley', 'Jonathan', 'Anna', 'Stephen', 'Brenda',
    'Larry', 'Pamela', 'Justin', 'Nicole', 'Scott', 'Emma', 'Brandon', 'Helen',
    'Benjamin', 'Samantha', 'Samuel', 'Olivia', 'Frank', 'Sophia', 'Gregory', 'Grace',
    'Raymond', 'Chloe', 'Alexander', 'Victoria', 'Patrick', 'Rachel', 'Jack', 'Ella',
    'Dennis', 'Maria', 'Jerry', 'Ava', 'Tyler', 'Hannah', 'Aaron', 'Lily',
    'Priya', 'Raj', 'Ananya', 'Arjun', 'Mei', 'Chen', 'Yuki', 'Hiroshi',
    'Amara', 'Kwame', 'Sofia', 'Diego', 'Lucia', 'Mateo', 'Elena', 'Lucas',
]

LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
    'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas',
    'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson', 'White',
    'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker', 'Young',
    'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores',
    'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell',
    'Carter', 'Roberts', 'Gomez', 'Phillips', 'Evans', 'Turner', 'Diaz', 'Parker',
    'Cruz', 'Edwards', 'Collins', 'Reyes', 'Stewart', 'Morris', 'Morales', 'Murphy',
    'Cook', 'Rogers', 'Gutierrez', 'Ortiz', 'Morgan', 'Cooper', 'Peterson', 'Bailey',
    'Reed', 'Kelly', 'Howard', 'Ramos', 'Kim', 'Cox', 'Ward', 'Richardson',
    'Watson', 'Brooks', 'Chavez', 'Wood', 'James', 'Bennett', 'Gray', 'Mendoza',
    'Ruiz', 'Hughes', 'Price', 'Alvarez', 'Castillo', 'Sanders', 'Patel', 'Myers',
    'Long', 'Ross', 'Foster', 'Jimenez', 'Powell', 'Jenkins', 'Perry', 'Russell',
    'Sullivan', 'Bell', 'Coleman', 'Butler', 'Henderson', 'Simmons', 'Barnes', 'Rossi',
    'Murakami', 'Nakamura', 'Park', 'Khan', 'Okafor', 'Silva', 'Costa', 'Fernandez',
]

# Vocabulary buckets so cosine similarity finds plausible neighbours per category name
TOPIC_LEXICON = {
    'Technology': [
        'software', 'cloud', 'developer', 'api', 'security', 'hardware', 'database',
        'algorithm', 'deployment', 'latency', 'kubernetes', 'container', 'network',
    ],
    'Lifestyle': [
        'routine', 'wellness', 'habits', 'morning', 'evening', 'balance', 'mindful',
        'community', 'family', 'home', 'space', 'comfort', 'seasonal', 'simple',
    ],
    'Travel': [
        'journey', 'itinerary', 'flight', 'hotel', 'landscape', 'coastal', 'mountain',
        'culture', 'local', 'guide', 'passport', 'adventure', 'city', 'region',
    ],
    'Food': [
        'recipe', 'ingredient', 'kitchen', 'flavor', 'seasoning', 'baking', 'grill',
        'organic', 'market', 'dinner', 'brunch', 'dessert', 'sauce', 'aroma',
    ],
    'Health': [
        'fitness', 'recovery', 'sleep', 'nutrition', 'hydration', 'training', 'cardio',
        'strength', 'clinic', 'research', 'prevention', 'mental', 'energy', 'habit',
    ],
    'Science': [
        'experiment', 'hypothesis', 'data', 'analysis', 'theory', 'lab', 'sample',
        'measurement', 'evidence', 'review', 'model', 'field', 'observation', 'study',
    ],
    'Art': [
        'studio', 'exhibition', 'palette', 'sculpture', 'gallery', 'creative', 'design',
        'composition', 'texture', 'color', 'craft', 'artist', 'collection', 'form',
    ],
    'Sports': [
        'season', 'training', 'match', 'stadium', 'coach', 'team', 'league', 'fitness',
        'strategy', 'endurance', 'tournament', 'athlete', 'performance', 'record',
    ],
    'Business': [
        'strategy', 'market', 'customer', 'revenue', 'growth', 'operations', 'planning',
        'partnership', 'investment', 'product', 'service', 'team', 'delivery', 'value',
    ],
    'Education': [
        'curriculum', 'student', 'teacher', 'lesson', 'practice', 'skill', 'course',
        'assessment', 'feedback', 'learning', 'classroom', 'study', 'campus', 'degree',
    ],
    'Other': [
        'story', 'thought', 'reflection', 'update', 'community', 'note', 'idea',
        'discussion', 'perspective', 'experience', 'moment', 'detail', 'context',
    ],
}


def _random_password(length=14):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def _make_placeholder_image():
    img = Image.new(
        'RGB',
        (720, 400),
        (random.randint(40, 220), random.randint(40, 220), random.randint(40, 220)),
    )
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=88)
    buf.seek(0)
    return ContentFile(buf.read(), name=f'seed_{secrets.token_hex(6)}.jpg')


def _build_paragraph(category_name, rng):
    words = TOPIC_LEXICON.get(category_name, TOPIC_LEXICON['Other'])
    picks = [rng.choice(words) for _ in range(18)]
    filler = (
        'This article explores practical angles and shares observations from recent work. '
        'Readers can use these ideas as starting points for their own projects.'
    )
    body = filler + ' Key themes include ' + ', '.join(picks[:10]) + '. '
    body += 'We also connect ' + ', '.join(picks[10:14]) + ' to everyday decisions. '
    body += 'Finally we highlight ' + ', '.join(picks[14:]) + ' for further reading.'
    return body


class Command(BaseCommand):
    help = 'Seed categories (if needed), demo users, 100+ posts, likes, follows; writes user.txt'

    def add_arguments(self, parser):
        parser.add_argument('--posts', type=int, default=DEFAULT_POST_COUNT, help='Number of demo posts to create')
        parser.add_argument('--writers', type=int, default=NUM_WRITERS)
        parser.add_argument('--readers', type=int, default=NUM_READERS)

    def handle(self, *args, **options):
        rng = random.Random(42)
        post_target = max(101, options['posts'])
        n_writers = options['writers']
        n_readers = options['readers']

        self._ensure_categories()
        writers, readers, user_lines = self._ensure_users(n_writers, n_readers, rng)
        self._write_user_file(user_lines)

        created_posts = self._create_posts(post_target, writers, rng)
        self.stdout.write(self.style.SUCCESS(f'Created {created_posts} demo posts.'))

        lk = self._seed_likes(writers + readers, rng)
        fw = self._seed_follows(writers + readers, writers, rng)
        self.stdout.write(self.style.SUCCESS(f'Seeded {lk} likes and {fw} new follow relationships.'))

    def _ensure_categories(self):
        if Category.objects.exists():
            return
        names = list(TOPIC_LEXICON.keys())
        for name in names:
            Category.objects.create(name=name, description=f'Seed category: {name}')
        self.stdout.write(self.style.SUCCESS(f'Created {len(names)} categories.'))

    def _ensure_users(self, n_writers, n_readers, rng):
        lines = [
            '# StoryScroll demo accounts (generated by seed_demo_data)',
            '# Format: username | email | password | role | full_name',
            '',
        ]
        writers = []
        readers = []
        for i in range(1, n_writers + 1):
            username = f'story_writer_{i:02d}'
            email = f'story_writer_{i:02d}.{secrets.token_hex(4)}@storyscroll.demo'
            password = _random_password()
            first = rng.choice(FIRST_NAMES)
            last = rng.choice(LAST_NAMES)
            user, _ = User.objects.update_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first[:150],
                    'last_name': last[:150],
                    'role': 'Writer',
                    'is_approved': True,
                    'is_staff': False,
                    'is_superuser': False,
                },
            )
            user.set_password(password)
            user.save()
            full = f'{user.first_name} {user.last_name}'.strip()
            lines.append(f'{username} | {user.email} | {password} | Writer | {full}')
            writers.append(user)

        for i in range(1, n_readers + 1):
            username = f'story_reader_{i:02d}'
            email = f'story_reader_{i:02d}.{secrets.token_hex(4)}@storyscroll.demo'
            password = _random_password()
            first = rng.choice(FIRST_NAMES)
            last = rng.choice(LAST_NAMES)
            user, _ = User.objects.update_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first[:150],
                    'last_name': last[:150],
                    'role': 'Reader',
                    'is_approved': True,
                    'is_staff': False,
                    'is_superuser': False,
                },
            )
            user.set_password(password)
            user.save()
            full = f'{user.first_name} {user.last_name}'.strip()
            lines.append(f'{username} | {user.email} | {password} | Reader | {full}')
            readers.append(user)

        return writers, readers, lines

    def _write_user_file(self, lines):
        path = Path(settings.BASE_DIR) / 'user.txt'
        path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        self.stdout.write(self.style.SUCCESS(f'Wrote credentials to {path}'))

    def _create_posts(self, post_target, writers, rng):
        category_names = list(Category.objects.values_list('name', flat=True))
        if not category_names:
            category_names = ['Other']

        existing_demo = Post.objects.filter(title__startswith='[Demo]').count()
        to_create = max(0, post_target - existing_demo)
        if to_create == 0:
            self.stdout.write('Enough demo posts already exist (title prefix [Demo]). Skipping posts.')
            return 0

        for n in range(to_create):
            author = rng.choice(writers)
            cat = rng.choice(category_names)
            title = f'[Demo] {cat} notes {secrets.token_hex(3)} — insight {n + 1}'
            body = _build_paragraph(cat, rng)
            post = Post.objects.create(
                title=title[:200],
                content=body,
                category=cat,
                author=author,
            )
            img = _make_placeholder_image()
            post.featured_image.save(img.name, img, save=True)
        return to_create

    def _seed_likes(self, all_users, rng):
        posts = list(Post.objects.filter(title__startswith='[Demo]'))
        if not posts or not all_users:
            return 0
        created = 0
        for _ in range(NUM_LIKE_ACTIONS):
            user = rng.choice(all_users)
            post = rng.choice(posts)
            _, was_created = Like.objects.get_or_create(post=post, user=user)
            if was_created:
                created += 1
        return created

    def _seed_follows(self, all_users, writers, rng):
        writers = [w for w in writers if w.role == 'Writer']
        followers = [u for u in all_users if u.role in ('Reader', 'Writer')]
        if not writers or not followers:
            return 0
        created = 0
        for _ in range(NUM_FOLLOW_ACTIONS):
            follower = rng.choice(followers)
            author = rng.choice(writers)
            if follower.id == author.id:
                continue
            _, was_created = Follow.objects.get_or_create(follower=follower, followed_author=author)
            if was_created:
                created += 1
        return created

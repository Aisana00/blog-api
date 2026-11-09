# Python modules
import random
import time
from typing import Any

# Third-party modules
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import (
    BaseCommand,
    CommandError,
    CommandParser,
)
from django.db import transaction
from django.utils.text import slugify
from faker import Faker

# Project modules
from apps.blog.models import Category, Comment, Post, Tag

User = get_user_model()
fake = Faker()

DEFAULT_USERS = 20
DEFAULT_POSTS = 100
DEFAULT_COMMENTS = 500

SEED_PASSWORD = "seedpass123"

INACTIVE_USERS_RATIO = 0.1
STAFF_USERS_RATIO = 0.05
PUBLISHED_POSTS_RATIO = 0.7
NO_CATEGORY_RATIO = 0.1

MIN_TAGS = 0
MAX_TAGS = 5
MIN_PARAGRAPHS = 3
MAX_PARAGRAPHS = 6
MIN_COMMENT_SENTENCES = 1
MAX_COMMENT_SENTENCES = 3
TITLE_WORDS = 6

FIRST_SUFFIX = 2
SLUG_SUFFIX_RESERVE = 6

LABEL_WIDTH = 12
COUNT_WIDTH = 5

EMAIL_DOMAINS = ("example.com", "gmail.com", "kbtu.kz")

CATEGORY_NAMES = (
    "Python",
    "Django",
    "DevOps",
    "JavaScript",
    "Databases",
    "Machine Learning",
    "Security",
    "Career",
)
TAG_NAMES = (
    "Python",
    "Django",
    "DRF",
    "REST API",
    "PostgreSQL",
    "Docker",
    "Kubernetes",
    "Git",
    "Linux",
    "Testing",
    "Pytest",
    "Celery",
    "Redis",
    "Nginx",
    "AWS",
    "React",
    "TypeScript",
    "SQL",
    "ORM",
    "Tips",
)


class Command(BaseCommand):
    """Fill the database with fake data."""

    help = "Fill the database with fake data."

    def add_arguments(self, parser: CommandParser) -> None:
        """Describe command arguments."""
        parser.add_argument(
            "--users",
            type=int,
            default=DEFAULT_USERS,
            help="Number of users to create",
        )
        parser.add_argument(
            "--posts",
            type=int,
            default=DEFAULT_POSTS,
            help="Number of posts to create",
        )
        parser.add_argument(
            "--comments",
            type=int,
            default=DEFAULT_COMMENTS,
            help="Number of comments to create",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing data before seeding",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Command entry point."""
        users_count: int = options["users"]
        posts_count: int = options["posts"]
        comments_count: int = options["comments"]
        clear: bool = options["clear"]

        self._validate_counts(
            users=users_count,
            posts=posts_count,
            comments=comments_count,
        )

        start_time: float = time.perf_counter()

        with transaction.atomic():
            if clear:
                self._clear_data()
            users_created: int = self._create_users(users_count)
            categories_created: int = self._create_named(
                Category, CATEGORY_NAMES
            )
            tags_created: int = self._create_named(Tag, TAG_NAMES)
            posts_created: int = self._create_posts(posts_count)
            comments_created: int = self._create_comments(comments_count)

        elapsed: float = time.perf_counter() - start_time

        summary: tuple[tuple[str, int], ...] = (
            ("Users", users_created),
            ("Categories", categories_created),
            ("Tags", tags_created),
            ("Posts", posts_created),
            ("Comments", comments_created),
        )
        label: str
        value: int
        for label, value in summary:
            self.stdout.write(
                f"{label + ':':<{LABEL_WIDTH}}{value:>{COUNT_WIDTH}} created"
            )
        self.stdout.write(self.style.SUCCESS(f"Done in {elapsed:.2f} seconds"))

    def _validate_counts(self, **counts: int) -> None:
        """Raise an error if any number is negative."""
        name: str
        value: int
        for name, value in counts.items():
            if value < 0:
                raise CommandError(
                    f"--{name} must be 0 or greater, got {value}."
                )

    def _clear_data(self) -> None:
        """Delete all seeded data, but keep superusers."""
        Comment.objects.all().delete()
        Post.objects.all().delete()
        Tag.objects.all().delete()
        Category.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.WARNING("Existing data deleted."))

    def _build_unique_email(
        self,
        first_name: str,
        last_name: str,
        used_emails: set[str],
    ) -> str:
        """Build email from names: emily.johnson@example.com."""
        local_part: str = f"{slugify(first_name)}.{slugify(last_name)}"
        domain: str = random.choice(EMAIL_DOMAINS)
        email: str = f"{local_part}@{domain}"
        suffix: int = FIRST_SUFFIX
        while email in used_emails:
            email = f"{local_part}{suffix}@{domain}"
            suffix += 1
        used_emails.add(email)
        return email

    def _create_users(self, count: int) -> int:
        """Create users with one hashed password."""
        if count == 0:
            return 0

        password_hash: str = make_password(SEED_PASSWORD)
        used_emails: set[str] = set(
            User.objects.values_list("email", flat=True)
        )

        users: list[Any] = []
        for _ in range(count):
            first_name: str = fake.first_name()
            last_name: str = fake.last_name()
            users.append(
                User(
                    email=self._build_unique_email(
                        first_name, last_name, used_emails
                    ),
                    first_name=first_name,
                    last_name=last_name,
                    password=password_hash,
                    is_active=random.random() >= INACTIVE_USERS_RATIO,
                    is_staff=random.random() < STAFF_USERS_RATIO,
                )
            )

        User.objects.bulk_create(users)
        return len(users)

    def _create_named(
        self,
        model: type[Category] | type[Tag],
        names: tuple[str, ...],
    ) -> int:
        """Create categories or tags that do not exist yet."""
        existing_slugs: set[str] = set(
            model.objects.values_list("slug", flat=True)
        )
        new_objects: list[Any] = [
            model(name=name, slug=slugify(name))
            for name in names
            if slugify(name) not in existing_slugs
        ]
        model.objects.bulk_create(new_objects)
        return len(new_objects)

    def _build_unique_slug(
        self,
        title: str,
        used_slugs: set[str],
        max_length: int,
    ) -> str:
        """Make slug unique: my-post, my-post-2, my-post-3."""
        base: str = slugify(title)[: max_length - SLUG_SUFFIX_RESERVE]
        base = base.strip("-")
        slug: str = base
        suffix: int = FIRST_SUFFIX
        while slug in used_slugs:
            slug = f"{base}-{suffix}"
            suffix += 1
        used_slugs.add(slug)
        return slug

    def _pick_category(self, categories: list[Category]) -> Category | None:
        """About 10% of posts have no category."""
        if not categories or random.random() < NO_CATEGORY_RATIO:
            return None
        return random.choice(categories)

    def _pick_status(self) -> str:
        """About 70% published, 30% draft."""
        if random.random() < PUBLISHED_POSTS_RATIO:
            return Post.Status.PUBLISHED
        return Post.Status.DRAFT

    def _create_posts(self, count: int) -> int:
        """Create posts and attach random tags."""
        if count == 0:
            return 0

        authors: list[Any] = list(User.objects.all())
        if not authors:
            raise CommandError(
                "Cannot create posts: there are no users. "
                "Run with --users N first."
            )

        categories: list[Category] = list(Category.objects.all())
        tags: list[Tag] = list(Tag.objects.all())
        used_slugs: set[str] = set(Post.objects.values_list("slug", flat=True))
        slug_max_length: int = Post._meta.get_field("slug").max_length

        posts: list[Post] = []
        for _ in range(count):
            title: str = fake.sentence(nb_words=TITLE_WORDS).rstrip(".")
            paragraphs: list[str] = fake.paragraphs(
                nb=random.randint(MIN_PARAGRAPHS, MAX_PARAGRAPHS)
            )
            posts.append(
                Post(
                    author=random.choice(authors),
                    title=title,
                    slug=self._build_unique_slug(
                        title, used_slugs, slug_max_length
                    ),
                    body="\n\n".join(paragraphs),
                    category=self._pick_category(categories),
                    status=self._pick_status(),
                )
            )

        Post.objects.bulk_create(posts)

        post: Post
        for post in posts:
            tags_count: int = random.randint(
                MIN_TAGS, min(MAX_TAGS, len(tags))
            )
            post.tags.set(random.sample(tags, tags_count))

        return len(posts)

    def _create_comments(self, count: int) -> int:
        """Create comments only on published posts."""
        if count == 0:
            return 0

        authors: list[Any] = list(User.objects.all())
        if not authors:
            raise CommandError(
                "Cannot create comments: there are no users. "
                "Run with --users N first."
            )

        published_posts: list[Post] = list(
            Post.objects.filter(status=Post.Status.PUBLISHED)
        )
        if not published_posts:
            raise CommandError(
                "Cannot create comments: there are no published posts. "
                "Run with --posts N first."
            )

        comments: list[Comment] = [
            Comment(
                post=random.choice(published_posts),
                author=random.choice(authors),
                body=" ".join(
                    fake.sentences(
                        nb=random.randint(
                            MIN_COMMENT_SENTENCES, MAX_COMMENT_SENTENCES
                        )
                    )
                ),
            )
            for _ in range(count)
        ]
        Comment.objects.bulk_create(comments)
        return len(comments)
"""Run ORM queries from apps/blog/queries.py."""

from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import connection
from django.db.models import Count, Model, QuerySet
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.blog.models import Category, Post, Tag
from apps.blog.queries import QUERIES

PREVIEW_ROWS = 5
WRITE_QUERIES = frozenset(range(40, 45))
SAMPLE_WORD = "a"
SAMPLE_PAGE = 1
SAMPLE_DAYS = 30
SAMPLE_MIN_POSTS = 2
SAMPLE_OLD_DRAFT_DAYS = 30
SAMPLE_TAG_NAME = "Django ORM"
SAMPLE_NAME_PART_LENGTH = 3
MIN_TAGS_FOR_PAIR = 2


def build_arguments() -> dict[int, dict[str, Any]]:
    """Sample arguments for queries that need them."""
    post = Post.objects.select_related("author").first()
    email = post.author.email if post else ""
    first_name = post.author.first_name if post else ""
    categories = list(
        Category.objects.annotate(n=Count("posts"))
        .filter(n__gt=0)
        .values_list("slug", flat=True)[:2]
    ) or [""]
    tags = list(Tag.objects.values_list("slug", flat=True)[:2]) or [""]
    pair_post = (
        Post.objects.annotate(n=Count("tags"))
        .filter(n__gte=MIN_TAGS_FOR_PAIR)
        .prefetch_related("tags")
        .first()
    )
    pair = [tag.slug for tag in pair_post.tags.all()[:2]] if pair_post else tags
    today = timezone.localdate()
    return {
        4: {"slug": post.slug if post else ""},
        7: {"page": SAMPLE_PAGE},
        8: {"word": SAMPLE_WORD},
        9: {"domain": email.split("@")[-1]},
        11: {"slugs": categories},
        12: {"year": today.year, "month": today.month},
        13: {"days": SAMPLE_DAYS},
        14: {"start": today.replace(day=1), "end": today},
        15: {"email": email.upper()},
        16: {"tag_slug": tags[0]},
        17: {"category_slug": categories[0]},
        21: {"first_slug": pair[0], "second_slug": pair[-1]},
        22: {"text": SAMPLE_WORD},
        34: {"min_posts": SAMPLE_MIN_POSTS},
        37: {"text": first_name[:SAMPLE_NAME_PART_LENGTH]},
        40: {"name": SAMPLE_TAG_NAME},
        41: {"days": SAMPLE_OLD_DRAFT_DAYS},
        42: {"category_slug": categories[0], "tag_slug": tags[0]},
        43: {"source_slug": categories[0], "target_slug": categories[-1]},
    }


class Command(BaseCommand):
    """Run the homework queries."""

    help = "Run ORM queries and show results and SQL count."

    def add_arguments(self, parser: CommandParser) -> None:
        """Add --number and --sql options."""
        parser.add_argument("--number", type=int, help="Run only this query.")
        parser.add_argument("--sql", action="store_true", help="Print the SQL.")

    def handle(self, *args: Any, **options: Any) -> None:
        """Run one query or all read queries."""
        number = options["number"]
        if number is not None and number not in QUERIES:
            raise CommandError(f"Query #{number} does not exist.")
        if number is not None:
            numbers = [number]
        else:
            numbers = [n for n in QUERIES if n not in WRITE_QUERIES]
        arguments = build_arguments()
        for current in numbers:
            self.run_query(current, arguments.get(current, {}), options["sql"])

    def run_query(
        self, number: int, arguments: dict[str, Any], show_sql: bool
    ) -> None:
        """Run one query and print the result."""
        function = QUERIES[number]
        annotations: list[str] = []
        with CaptureQueriesContext(connection) as context:
            result = function(**arguments)
            if isinstance(result, QuerySet):
                annotations = list(result.query.annotations)
                result = list(result)
        count = len(context.captured_queries)
        word = "query" if count == 1 else "queries"
        self.stdout.write(
            self.style.SUCCESS(f"#{number} {function.__name__} — {count} SQL {word}")
        )
        if show_sql:
            for captured in context.captured_queries:
                self.stdout.write(captured["sql"])
        self.write_result(result, annotations)

    def write_result(self, result: Any, annotations: list[str]) -> None:
        """Print the first rows and the total."""
        if isinstance(result, dict):
            rows = [f"{key}: {value}" for key, value in result.items()]
        elif isinstance(result, list):
            rows = [self.format_row(row, annotations) for row in result]
        else:
            self.stdout.write(f"  {self.format_row(result, annotations)}")
            return
        for row in rows[:PREVIEW_ROWS]:
            self.stdout.write(f"  {row}")
        self.stdout.write(f"  ({len(rows)} rows)")

    @staticmethod
    def format_row(row: Any, annotations: list[str]) -> str:
        """Format one row with its annotated values."""
        if isinstance(row, Model) and annotations:
            extra = {name: getattr(row, name) for name in annotations}
            return f"{row} {extra}"
        return str(row)

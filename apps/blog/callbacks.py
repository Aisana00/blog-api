# Python modules
import json
from typing import Any

# Third-party modules
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.http import HttpRequest

# Project modules
from apps.blog.models import Category, Comment, Post
from settings.conf import ENV_ID

User = get_user_model()

PROD_ENV_ID = "prod"
TOP_AUTHORS_LIMIT = 5
PERCENT = 100


def environment_callback(request: HttpRequest) -> list[str]:
    """Badge near the title: Local (orange) or Production (red)."""
    if ENV_ID == PROD_ENV_ID:
        return ["Production", "danger"]
    return ["Local", "warning"]


def drafts_badge(request: HttpRequest) -> int:
    """Number of drafts next to Posts in the sidebar."""
    return Post.objects.filter(status=Post.Status.DRAFT).count()


def dashboard_callback(
    request: HttpRequest,
    context: dict[str, Any],
) -> dict[str, Any]:
    """Add dashboard data to the admin home page."""
    published_count: int = Post.objects.filter(
        status=Post.Status.PUBLISHED
    ).count()
    drafts_count: int = Post.objects.filter(status=Post.Status.DRAFT).count()
    posts_total: int = published_count + drafts_count

    categories = Category.objects.annotate(
        total_posts=Count("posts")
    ).order_by("-total_posts")
    chart_data: str = json.dumps(
        {
            "labels": [category.name for category in categories],
            "datasets": [
                {
                    "label": "Posts",
                    "data": [category.total_posts for category in categories],
                    "backgroundColor": "var(--color-primary-600)",
                },
            ],
        }
    )

    top_authors = User.objects.annotate(
        total_posts=Count("posts")
    ).order_by("-total_posts")[:TOP_AUTHORS_LIMIT]
    top_authors_table: dict[str, list[Any]] = {
        "headers": ["Author", "Email", "Posts"],
        "rows": [
            [
                f"{author.first_name} {author.last_name}",
                author.email,
                author.total_posts,
            ]
            for author in top_authors
        ],
    }

    published_percent: int = (
        round(published_count * PERCENT / posts_total) if posts_total else 0
    )

    context.update(
        {
            "cards": [
                {"title": "Users", "value": User.objects.count()},
                {"title": "Published posts", "value": published_count},
                {"title": "Drafts", "value": drafts_count},
                {"title": "Comments", "value": Comment.objects.count()},
            ],
            "chart_data": chart_data,
            "top_authors_table": top_authors_table,
            "published_percent": published_percent,
            "drafts_percent": PERCENT - published_percent if posts_total else 0,
            "published_text": f"{published_count} of {posts_total}",
            "drafts_text": f"{drafts_count} of {posts_total}",
        }
    )
    return context
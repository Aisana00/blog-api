# Third-party modules
from django.contrib import admin, messages
from django.db.models import Count, Prefetch, QuerySet, TextField
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.text import Truncator
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    AutocompleteSelectFilter,
    ChoicesDropdownFilter,
    MultipleRelatedDropdownFilter,
    RangeDateTimeFilter,
    RelatedDropdownFilter,
)
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.decorators import action, display
from unfold.sections import TableSection

# Project modules
from apps.blog.models import Category, Comment, Post, Tag

BODY_PREVIEW_LENGTH = 50
COMMENTS_PER_PAGE = 10
SECTION_HEIGHT = 300

POST_CHANGELIST_URL = "admin:blog_post_changelist"
COMMENT_CHANGELIST_URL = "admin:blog_comment_changelist"


# ----------------------------------------------
# Sections (row expands on click)
#
class CategoryPostsSection(TableSection):
    """Posts of the category under the row."""

    verbose_name = "Posts"
    related_name = "posts"
    fields = ("title", "status", "created_at")
    height = SECTION_HEIGHT


class PostCommentsSection(TableSection):
    """Comments of the post under the row."""

    verbose_name = "Comments"
    related_name = "comments"
    fields = ("author", "body", "created_at")
    height = SECTION_HEIGHT


# ----------------------------------------------
# Category and Tag
#
@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    """Category admin."""

    list_display = ("name", "slug", "posts_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    list_sections = (CategoryPostsSection,)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Category]:
        """Count posts with one query."""
        return (
            super()
            .get_queryset(request)
            .annotate(total_posts=Count("posts", distinct=True))
            .prefetch_related("posts")
        )

    @display(description="Posts", ordering="total_posts")
    def posts_count(self, obj: Category) -> int:
        """Number of posts (from annotate)."""
        return obj.total_posts


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    """Tag admin."""

    list_display = ("name", "slug", "posts_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request: HttpRequest) -> QuerySet[Tag]:
        """Count posts with one query."""
        return (
            super()
            .get_queryset(request)
            .annotate(total_posts=Count("posts", distinct=True))
        )

    @display(description="Posts", ordering="total_posts")
    def posts_count(self, obj: Tag) -> int:
        """Number of posts (from annotate)."""
        return obj.total_posts


# ----------------------------------------------
# Comment
#
@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    """Comment admin."""

    list_display = ("post_title", "author", "short_body", "created_at")
    list_filter = (
        ("post", AutocompleteSelectFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    )
    list_filter_submit = True
    search_fields = ("body", "author__email", "post__title")
    autocomplete_fields = ("post", "author")
    list_select_related = ("post", "author")

    @display(description="Post", ordering="post__title")
    def post_title(self, obj: Comment) -> str:
        """Title of the post."""
        return obj.post.title

    @display(description="Body")
    def short_body(self, obj: Comment) -> str:
        """Body shortened to N characters."""
        return Truncator(obj.body).chars(BODY_PREVIEW_LENGTH)


# ----------------------------------------------
# Post
#
class CommentInline(TabularInline):
    """Comments inside the post page, in their own tab."""

    model = Comment
    fields = ("author", "body", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("author",)
    extra = 0
    tab = True
    per_page = COMMENTS_PER_PAGE


@admin.register(Post)
class PostAdmin(ModelAdmin):
    """Post admin: the main showcase."""

    list_display = (
        "display_header",
        "status_label",
        "category",
        "display_tags",
        "comments_count",
        "created_at",
    )
    list_filter = (
        ("status", ChoicesDropdownFilter),
        ("category", RelatedDropdownFilter),
        ("tags", MultipleRelatedDropdownFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    )
    list_filter_submit = True
    search_fields = ("title", "body", "author__email")
    list_select_related = ("author", "category")
    list_sections = (PostCommentsSection,)

    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("author", "category", "tags")
    readonly_fields = ("created_at", "updated_at")
    inlines = (CommentInline,)
    warn_unsaved_form = True
    formfield_overrides = {
        TextField: {"widget": WysiwygWidget},
    }

    fieldsets = (
        (
            "Content",
            {"classes": ["tab"], "fields": ("title", "slug", "body")},
        ),
        (
            "Classification",
            {"classes": ["tab"], "fields": ("category", "tags", "status")},
        ),
        (
            "Meta",
            {
                "classes": ["tab"],
                "fields": ("author", "created_at", "updated_at"),
            },
        ),
    )

    actions = ("publish_selected", "move_to_drafts")
    actions_list = ("publish_all_drafts",)
    actions_row = ("toggle_status",)
    actions_detail = ("open_comments",)
    actions_submit_line = ("save_and_publish",)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Post]:
        """No N+1: count comments, prefetch tags and comments."""
        return (
            super()
            .get_queryset(request)
            .annotate(total_comments=Count("comments", distinct=True))
            .prefetch_related(
                "tags",
                Prefetch(
                    "comments",
                    queryset=Comment.objects.select_related("author"),
                ),
            )
        )

    # ---------- columns ----------
    @display(description="Post", header=True, ordering="title")
    def display_header(self, obj: Post) -> list[str]:
        """Title and author."""
        initials: str = (
            f"{obj.author.first_name[:1]}{obj.author.last_name[:1]}".upper()
        )
        return [obj.title, obj.author.email, initials]

    @display(
        description="Status",
        label={
            Post.Status.PUBLISHED: "success",
            Post.Status.DRAFT: "warning",
        },
    )
    def status_label(self, obj: Post) -> tuple[str, str]:
        """Green published, orange draft."""
        return obj.status, obj.get_status_display()

    @display(description="Tags", dropdown=True)
    def display_tags(self, obj: Post) -> dict[str, object]:
        """Tags as a dropdown (len, not count: uses prefetch)."""
        tags: list[Tag] = list(obj.tags.all())
        return {
            "title": f"{len(tags)} tags",
            "items": [{"title": tag.name} for tag in tags],
            "striped": True,
        }

    @display(description="Comments", ordering="total_comments")
    def comments_count(self, obj: Post) -> int:
        """Number of comments (from annotate)."""
        return obj.total_comments

    # ---------- bulk actions ----------
    @action(description="Publish selected")
    def publish_selected(
        self, request: HttpRequest, queryset: QuerySet[Post]
    ) -> None:
        """Publish checked posts."""
        updated: int = queryset.update(status=Post.Status.PUBLISHED)
        self.message_user(
            request, f"{updated} posts published.", messages.SUCCESS
        )

    @action(description="Move to drafts")
    def move_to_drafts(
        self, request: HttpRequest, queryset: QuerySet[Post]
    ) -> None:
        """Move checked posts to drafts."""
        updated: int = queryset.update(status=Post.Status.DRAFT)
        self.message_user(
            request, f"{updated} posts moved to drafts.", messages.WARNING
        )

    # ---------- button above the list ----------
    @action(description="Publish all drafts", url_path="publish-all-drafts")
    def publish_all_drafts(self, request: HttpRequest) -> HttpResponseRedirect:
        """Publish every draft."""
        updated: int = Post.objects.filter(status=Post.Status.DRAFT).update(
            status=Post.Status.PUBLISHED
        )
        self.message_user(
            request, f"{updated} drafts published.", messages.SUCCESS
        )
        return redirect(reverse(POST_CHANGELIST_URL))

    # ---------- button in every row ----------
    @action(description="Publish / Unpublish", url_path="toggle-status")
    def toggle_status(
        self, request: HttpRequest, object_id: int
    ) -> HttpResponseRedirect:
        """Switch status of one post."""
        post: Post = get_object_or_404(Post, pk=object_id)
        if post.status == Post.Status.PUBLISHED:
            post.status = Post.Status.DRAFT
        else:
            post.status = Post.Status.PUBLISHED
        post.save(update_fields=["status", "updated_at"])
        self.message_user(
            request,
            f"«{post.title}» is now {post.get_status_display()}.",
            messages.SUCCESS,
        )
        return redirect(
            request.META.get("HTTP_REFERER", reverse(POST_CHANGELIST_URL))
        )

    # ---------- button on the post page ----------
    @action(description="Open comments", url_path="open-comments")
    def open_comments(
        self, request: HttpRequest, object_id: int
    ) -> HttpResponseRedirect:
        """Go to comments of this post."""
        return redirect(
            f"{reverse(COMMENT_CHANGELIST_URL)}?post__id__exact={object_id}"
        )

    # ---------- button next to Save ----------
    @action(description="Save & publish")
    def save_and_publish(self, request: HttpRequest, obj: Post) -> None:
        """Runs after the object is saved."""
        obj.status = Post.Status.PUBLISHED
        obj.save(update_fields=["status", "updated_at"])
        self.message_user(request, "Post saved and published.")
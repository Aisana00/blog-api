# Third-party modules
from django.contrib import admin, messages
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count, QuerySet
from django.http import HttpRequest
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import BooleanRadioFilter
from unfold.decorators import action, display
from unfold.forms import AdminPasswordChangeForm

# Project modules
from apps.auths.forms import CustomUserChangeForm, CustomUserCreationForm
from apps.auths.models import User

YES = "yes"
NO = "no"

admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    """Django groups with the Unfold look."""


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    """User admin: login by email, no username."""

    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = (
        "display_header",
        "display_active",
        "display_staff",
        "posts_count",
    )
    list_filter = (
        ("is_active", BooleanRadioFilter),
        ("is_staff", BooleanRadioFilter),
    )
    list_filter_submit = True
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    readonly_fields = ("last_login",)
    filter_horizontal = ("groups", "user_permissions")
    actions = ("activate_users", "deactivate_users")

    fieldsets = (
        (
            "Personal info",
            {
                "classes": ["tab"],
                "fields": ("email", "password", "first_name", "last_name"),
            },
        ),
        (
            "Permissions",
            {
                "classes": ["tab"],
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Important dates",
            {
                "classes": ["tab"],
                "fields": ("last_login",),
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[User]:
        """Count posts with one query."""
        return (
            super()
            .get_queryset(request)
            .annotate(total_posts=Count("posts", distinct=True))
        )

    @display(description="User", header=True, ordering="email")
    def display_header(self, obj: User) -> list[str]:
        """Full name, email and initials in a circle."""
        initials: str = f"{obj.first_name[:1]}{obj.last_name[:1]}".upper()
        return [f"{obj.first_name} {obj.last_name}", obj.email, initials]

    @display(description="Active", label={YES: "success", NO: "danger"})
    def display_active(self, obj: User) -> tuple[str, str]:
        """Green or red label."""
        if obj.is_active:
            return YES, "Active"
        return NO, "Inactive"

    @display(description="Staff", label={YES: "info", NO: "warning"})
    def display_staff(self, obj: User) -> tuple[str, str]:
        """Blue or orange label."""
        if obj.is_staff:
            return YES, "Staff"
        return NO, "User"

    @display(description="Posts", ordering="total_posts")
    def posts_count(self, obj: User) -> int:
        """Number of posts (from annotate)."""
        return obj.total_posts

    @action(description="Activate selected users")
    def activate_users(
        self, request: HttpRequest, queryset: QuerySet[User]
    ) -> None:
        """Activate with one query."""
        updated: int = queryset.update(is_active=True)
        self.message_user(
            request, f"{updated} users activated.", messages.SUCCESS
        )

    @action(description="Deactivate selected users")
    def deactivate_users(
        self, request: HttpRequest, queryset: QuerySet[User]
    ) -> None:
        """Deactivate with one query."""
        updated: int = queryset.update(is_active=False)
        self.message_user(
            request, f"{updated} users deactivated.", messages.WARNING
        )
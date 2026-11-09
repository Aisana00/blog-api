# Third-party modules
from unfold.forms import UserChangeForm, UserCreationForm

# Project modules
from apps.auths.models import User


class CustomUserCreationForm(UserCreationForm):
    """Add user form: email, names, password twice."""

    class Meta:
        """Form settings."""

        model = User
        fields = ("email", "first_name", "last_name")


class CustomUserChangeForm(UserChangeForm):
    """Edit user form."""

    class Meta:
        """Form settings."""

        model = User
        fields = "__all__"
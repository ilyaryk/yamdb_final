from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class RoleChoices(models.TextChoices):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class User(AbstractUser):
    "Класс переопределяет и расширяет стандартную модель User."

    USERNAME_ERR_MESS = (
        "Содержание поля 'username' не соответствует "
        "паттерну '^[\\w.@+-]+\\z'"
    )

    username = models.CharField(
        max_length=150,
        blank=False,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[\w.@+-]+\Z",
                message=USERNAME_ERR_MESS,
            )
        ],
    )
    email = models.EmailField(
        blank=False,
        unique=True,
        max_length=254,
    )
    first_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
    )
    bio = models.TextField(
        blank=True,
        null=True,
    )
    role = models.CharField(
        max_length=150,
        blank=False,
        choices=RoleChoices.choices,
        default=RoleChoices.USER,
    )

    @property
    def is_moderator(self):
        if self.role == RoleChoices.MODERATOR or self.is_staff:
            return True
        return False

    @property
    def is_admin(self):
        if self.role == RoleChoices.ADMIN or self.is_staff:
            return True
        return False

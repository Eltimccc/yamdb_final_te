import random

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from .validators import validate_username, validate_year
from api_yamdb.settings import USER, ADMIN, MODERATOR


ROLE_CHOICES = [(USER, USER), (ADMIN, ADMIN), (MODERATOR, MODERATOR)]


class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        null=False,
        validators=(validate_username,),
    )
    first_name = models.CharField("Имя", max_length=150, blank=True)
    last_name = models.CharField("Фамилия", max_length=150, blank=True)
    email = models.EmailField(max_length=254, unique=True, null=False)
    role = models.CharField(
        "Роль", max_length=10, choices=ROLE_CHOICES, default=USER, blank=True
    )
    bio = models.TextField(
        "Биография",
        blank=True,
    )
    confirmation_code = models.CharField(
        "Код подтверждения",
        max_length=255,
        null=True,
    )

    @property
    def is_user(self):
        return self.role == USER

    @property
    def is_admin(self):
        return self.role == ADMIN

    @property
    def is_moderator(self):
        return self.role == MODERATOR

    class Meta:
        ordering = ("username",)
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username


@receiver(post_save, sender=User)
def post_save(instance, created, **kwargs):
    if created:
        confirmation_code = "".join(
            random.sample(tuple(map(str, range(0, 10))), 4)
        )
        instance.confirmation_code = confirmation_code
        instance.save()


class Category(models.Model):
    name = models.CharField("Категория", max_length=256)
    slug = models.SlugField(
        "Slug категории",
        max_length=50,
        unique=True,
        db_index=True,
    )

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return f"{self.name} {self.name}"


class Genre(models.Model):
    name = models.CharField("Название жанра", max_length=200)
    slug = models.SlugField("Slug жанра", unique=True, db_index=True)

    class Meta:
        verbose_name = "Жанр"
        verbose_name_plural = "Жанры"

    def __str__(self):
        return self.name


class Title(models.Model):
    name = models.CharField("Название", max_length=200, db_index=True)
    year = models.IntegerField("Год", validators=(validate_year,))
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name="titles",
        verbose_name="Категория",
        null=True,
        blank=True,
    )
    description = models.TextField(
        "Описание", max_length=255, null=True, blank=True
    )
    genre = models.ManyToManyField(
        Genre, related_name="titles", verbose_name="Жанр"
    )

    class Meta:
        verbose_name = "Произведение"
        verbose_name_plural = "Произведения"

    def __str__(self):
        return self.name


class Review(models.Model):
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Произведение",
    )
    text = models.CharField(max_length=200)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Автор",
    )
    score = models.PositiveIntegerField(
        verbose_name="Оценка",
        validators=[
            MinValueValidator(1, "Нужна оценка от 1 до 10!"),
            MaxValueValidator(10, "Нужна оценка от 1 до 10!"),
        ],
    )
    pub_date = models.DateTimeField(
        "Дата публикации", auto_now_add=True, db_index=True
    )

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "title",
                    "author",
                ),
                name="unique-review",
            )
        ]
        ordering = ("pub_date",)

    def __str__(self):
        return self.text


class Comment(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Комментарий",
    )
    text = models.CharField("Текст комментария", max_length=200)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Автор",
    )
    pub_date = models.DateTimeField(
        "Дата публикации", auto_now_add=True, db_index=True
    )

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self):
        return self.text[:20]

from http import HTTPStatus

from django.core.mail import send_mail
from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from api_yamdb.settings import ADMIN_EMAIL, USER
from reviews.models import Category, Comment, Genre, Review, Title, User
from django.shortcuts import get_object_or_404

from .filters import TitleFilter
from .permissons import IsAdmin, IsAdminOrReadOnly, IsAuthorOrModerator
from .serializers import (
    AdminsSerializer,
    CategorySerializer,
    CommentSerializer,
    GenreSerializer,
    GetTokenSerializer,
    ReviewSerializer,
    SignUpSerializer,
    TitleAdminSerializer,
    TitleUserSerializer,
    UsersSerializer,
)


class UsersViewSet(viewsets.ModelViewSet):
    """
    UsersViewSet для получения

    Запрос (POST, PATCH):
    {
        "username": имя пользователя(:obj:`string`),
        "email": электронная почта пользователя(:obj:`string`).
    }

    Запрос (GET):
    {
        "username": имя пользователя(:obj:`string`).
    }

    Ответы:
    {
        "username": имя пользователя(:obj:`string`),
        "email": электронная почта пользователя(:obj:`string`),
        "first_name", "last_name": необязательные поля(:obj:`string`),
        "bio", "role": необязательные поля(:obj:`string`).

    }

    Запрос (DEL):
    {
        "username": имя пользователя(:obj:`string`).
    }

    """

    queryset = User.objects.all()
    serializer_class = AdminsSerializer
    permission_classes = (
        IsAuthenticated,
        IsAdmin,
    )
    lookup_field = "username"
    filter_backends = (SearchFilter,)
    search_fields = ("username",)

    @action(
        methods=("GET", "PATCH"),
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path="me",
    )
    def get_current_user_info(self, request):
        serializer = AdminsSerializer(request.user)
        if request.method == "PATCH":
            serializer = AdminsSerializer(
                request.user, data=request.data, partial=True
            )
            if request.user.is_admin:
                serializer = AdminsSerializer(
                    request.user, data=request.data, partial=True
                )
            else:
                serializer = UsersSerializer(
                    request.user, data=request.data, partial=True
                )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.data)


class APIGetToken(APIView):
    """
    APIView для получения токена.

    Запрос:
    {
        "username": имя пользователя(:obj:`string`),
        "confirmation_code": код доступа пользователя(:obj:`string`).
    }

    Ответ:
    {
        "token": токен(:obj:`string`).
    }
    """

    def post(self, request):
        serializer = GetTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = get_object_or_404(User, username=data["username"])

        if data.get("confirmation_code") == user.confirmation_code:
            token = RefreshToken.for_user(user).access_token
            return Response(
                {"token": str(token)}, status=status.HTTP_201_CREATED
            )

        return Response(
            {"confirmation_code": "Неверный код подтверждения!"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class APISignUp(APIView):
    """
    APIView для получения кода доступа (его отправка на email).

    Запрос:
    {
        "username": имя пользователя(:obj:`string`),
        "email": электронная почта пользователя(:obj:`string`).
    }
    """

    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        send_mail(
            "Код для API",
            (
                f"Здравствуйте, {user.username}!\n"
                f"Код доступа к API: {user.confirmation_code}"
            ),
            ADMIN_EMAIL,
            [user.email],
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


class CategoryViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet для работы с категориями.

    Получение списка всех категорий: GET /categories/

    Добавление новой категории POST /categories/:
    Запрос:
        {
            "name": название категории(:obj:`string`),
            "slug": slug категории(:obj:`string`).
        }
    Ответ:
        {
            "name": название категории(:obj:`string`),
            "slug": slug категории(:obj:`string`).
        }

    Удаление категории: DELETE /categories/{slug}/
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (SearchFilter,)
    search_fields = ("name",)
    lookup_field = "slug"


class GenreViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet для работы с жанрами.

    Получение списка всех жанров: GET /genres/

    Добавление жанра POST /genres/:
    Запрос:
    {
        "name": название жанра(:obj:`string`),
        "slug": slug жанра(:obj:`string`).
    }
    Ответ:
    {
        "name": название жанра(:obj:`string`),
        "slug": slug жанра(:obj:`string`).
    }

    Удаление жанра: DELETE /genres/{slug}/
    """

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (SearchFilter,)
    search_fields = ("name",)
    lookup_field = "slug"


class TitleViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с произведениями.

    Получение списка всех произведений: GET /titles/

    Добавление произведения POST /titles/:
    запрос:
    {
        "name": название произведения(:obj:`string`),
        "year": год релиза(:obj:`int`),
        "description": описание(:obj:`string`),
        "genre": жанры (:obj:`list[string]`),
        "category": название категории(:obj:`string`)/
    }
    ответ:
    {
        "id": id(:obj:`int`),
        "name": название произведения(:obj:`string`),
        "year": год релиза(:obj:`int`),
        "rating": рейтинг(:obj:`float`),
        "description": описание(:obj:`string`),
        "genre": жанры (:obj:`list[string]`),
        "category": название категории(:obj:`string`),
        "slug": slug произведения(:obj:`string`).
        }
    }

    Получение информации о произведении: GET /titles/{titles_id}/

    Частичное обновление информации о произведении: PATCH /titles/{titles_id}/

    Удаление произведения: DELETE /titles/{titles_id}/
    """

    queryset = queryset = Title.objects.annotate(
        rating=Avg("reviews__score")
    ).all()
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    pagination_class = PageNumberPagination
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return TitleUserSerializer
        return TitleAdminSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с отзывами.
    """

    serializer_class = ReviewSerializer
    pagination_class = PageNumberPagination
    permission_classes = (IsAuthorOrModerator,)

    def get_queryset(self):
        title_id = self.kwargs.get("title_id")
        pk = self.kwargs.get("pk")
        if not Title.objects.filter(id=title_id).exists():
            raise NotFound(
                detail="Произведение не найдено", code=HTTPStatus.NOT_FOUND
            )
        if pk and not Review.objects.filter(id=pk).exists():
            raise NotFound(detail="Отзыв не найден", code=HTTPStatus.NOT_FOUND)
        return Review.objects.filter(title_id=title_id)

    def perform_create(self, serializer):
        title_id = self.kwargs.get("title_id")
        text = self.request.data.get("text")
        score = self.request.data.get("score")
        if not Title.objects.filter(id=title_id).exists():
            raise NotFound(
                detail="Не найдено произведение!!!", code=HTTPStatus.NOT_FOUND
            )
        if Review.objects.filter(
            title_id=title_id, author=self.request.user
        ).exists():
            raise ParseError(
                detail="Нельзя добавить больше одного отзыва!",
                code=HTTPStatus.BAD_REQUEST,
            )
        serializer.save(
            title_id=title_id,
            text=text,
            score=score,
            author=self.request.user,
        )
        return Response(status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk, title_id):
        if not Title.objects.filter(id=title_id).exists():
            return Response(
                "Не найдено произведение!", status=status.HTTP_404_NOT_FOUND
            )
        review = Review.objects.filter(title=title_id, id=pk)
        if not review.exists():
            return Response(
                "Не найден отзыв!", status=status.HTTP_404_NOT_FOUND
            )
        review = review.first()
        cur_user = request.user
        review_author = review.author
        cur_user_group = cur_user.role
        if not request.data.get("text") and not request.data.get("score"):
            return Response(
                "Не передано ни одно из обязательных полей!",
                status=status.HTTP_400_BAD_REQUEST,
            )
        if cur_user_group == USER and cur_user != review_author:
            return Response(
                "Вы не можете редактировать чужой отзыв!",
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.serializer_class(
            review, data=self.request.data, partial=True
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk, title_id):
        if not Title.objects.filter(id=title_id).exists():
            return Response(
                "Не найдено произведение!", status=status.HTTP_404_NOT_FOUND
            )
        review = Review.objects.filter(title=title_id, id=pk)
        if not review.exists():
            return Response(
                "Отзыв не найден!", status=status.HTTP_404_NOT_FOUND
            )
        cur_user = request.user
        review = review.first()
        review_author = review.author
        cur_user_group = cur_user.role
        if cur_user_group == USER and cur_user != review_author:
            return Response(
                "Вы не можете удалить чужой отзыв!",
                status=status.HTTP_403_FORBIDDEN,
            )
        else:
            review.delete()
            return Response("Отзыв удален!", status=status.HTTP_204_NO_CONTENT)


class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с комментариями.
    """

    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = PageNumberPagination

    def get_queryset(self):
        title_id = self.kwargs.get("title_id")
        review_id = self.kwargs.get("review_id")
        comment_id = self.kwargs.get("pk")
        if not Review.objects.filter(id=review_id).exists():
            raise NotFound(detail="Не найден отзыв!", code=404)
        if not Title.objects.filter(id=title_id).exists():
            raise NotFound(
                detail="Не найдено произведение!", code=HTTPStatus.NOT_FOUND
            )
        if comment_id and not Comment.objects.filter(id=comment_id).exists():
            raise NotFound(
                detail="Не найден комментарий!", code=HTTPStatus.NOT_FOUND
            )
        return Comment.objects.filter(review=review_id)

    def perform_create(self, serializer):
        title_id = self.kwargs.get("title_id")
        review_id = self.kwargs.get("review_id")
        text = self.request.data.get("text")
        if not Title.objects.filter(id=title_id).exists():
            raise NotFound(
                detail="Не найдено произведение!", code=HTTPStatus.NOT_FOUND
            )
        if not Review.objects.filter(title_id=title_id, id=review_id).exists():
            raise NotFound(
                detail="Не найден отзыв!", code=HTTPStatus.NOT_FOUND
            )
        serializer.save(
            review_id=review_id, text=text, author=self.request.user
        )
        return Response(status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk, title_id, review_id):
        comment = Comment.objects.filter(id=pk, review_id=review_id)
        if not Title.objects.filter(id=title_id).exists():
            raise NotFound(
                detail="Не найдено произведение!", code=HTTPStatus.NOT_FOUND
            )
        if not Review.objects.filter(id=review_id).exists():
            raise NotFound(
                detail="Не найден отзыв!", code=HTTPStatus.NOT_FOUND
            )
        if not comment.exists():
            raise NotFound(
                detail="Не найден комментарий!", code=HTTPStatus.NOT_FOUND
            )

        cur_user = request.user
        cur_user_group = cur_user.role
        comment = comment.first()
        comment_author = comment.author
        if cur_user_group == USER and cur_user != comment_author:
            return Response(
                "Вы не можете редактировать чужой комментарий!",
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.serializer_class(
            comment, data=self.request.data, partial=True
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk, title_id, review_id):
        if not Title.objects.filter(id=title_id).exists():
            return Response(
                "Не найдено произведение!", status=status.HTTP_404_NOT_FOUND
            )
        if not Review.objects.filter(id=review_id, title_id=title_id).exists():
            return Response(
                "Не найден отзыв!", status=status.HTTP_404_NOT_FOUND
            )
        comment = Comment.objects.filter(id=pk, review_id=review_id)
        if not comment.exists():
            return Response(
                "Не найден комментарий!", status=status.HTTP_404_NOT_FOUND
            )
        cur_user = request.user
        cur_user_group = cur_user.role
        comment = comment.first()
        comment_author = comment.author
        if cur_user_group == USER and cur_user != comment_author:
            return Response(
                "Вы не можете удалить чужой комментарий!",
                status=status.HTTP_403_FORBIDDEN,
            )
        else:
            comment.delete()
            return Response(
                "Комментарий удален!", status=status.HTTP_204_NO_CONTENT
            )

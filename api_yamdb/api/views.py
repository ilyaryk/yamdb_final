from django.db.models import Avg
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import (
    filters,
    permissions,
    status,
    views,
    viewsets,
    mixins,
)
from rest_framework.pagination import LimitOffsetPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_simplejwt.tokens import RefreshToken

from .filters import TitleFilter
from .permissions import (
    AuthorModeratorOrReadOnly,
    IsAdmin,
)
from .serializers import (
    AuthSignupSerializer,
    GetJWTTokenSerializer,
    TitleSerializer,
    TitleListSerializer,
    GenreSerializer,
    UserViewSerializer,
    CategorySerializer,
    ReviewSerializer,
    CommentSerializer,
)
from users.models import User
from reviews.models import Category, Title, Genre, Review

EMAIL_TITLE = "Приветствуем {}"
EMAIL_MESSAGE = "Ваш секретный код: {}"


class MyMixinsSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
):
    pagination_class = LimitOffsetPagination
    permission_classes = (IsAdmin,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("name",)
    lookup_field = "slug"


class CategoryViewSet(MyMixinsSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action == "list" or self.action == "retrieve":
            return (permissions.AllowAny(),)

        return super().get_permissions()


class GenreViewSet(MyMixinsSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer

    def get_permissions(self):
        if self.action == "list" or self.action == "retrieve":
            return (permissions.AllowAny(),)

        return super().get_permissions()


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.annotate(rating=Avg("reviews__score"))
    serializer_class = TitleSerializer
    permission_classes = (IsAdmin,)
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action == "list" or self.action == "retrieve":
            return TitleListSerializer
        return TitleSerializer

    def get_permissions(self):
        if self.action == "list" or self.action == "retrieve":
            return (permissions.AllowAny(),)

        return super().get_permissions()


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (AuthorModeratorOrReadOnly | IsAdmin,)
    pagination_class = LimitOffsetPagination

    def get_title(self):
        return get_object_or_404(Title, id=self.kwargs.get("title_id"))

    def get_queryset(self):
        return self.get_title().reviews.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, title=self.get_title())

    def get_serializer_context(self):
        return {
            "title_id": self.kwargs.get("title_id"),
            "request": self.request,
        }


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (AuthorModeratorOrReadOnly | IsAdmin,)
    pagination_class = LimitOffsetPagination

    def get_review(self):
        return get_object_or_404(
            Review,
            id=self.kwargs.get("review_id"),
            title_id=self.kwargs.get("title_id"),
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, review=self.get_review())

    def get_queryset(self):
        return self.get_review().comments.all()


class AuthSignupView(views.APIView):
    """Класс для регистрации новых пользователей."""

    def post(self, request):
        username_and_email_exists = User.objects.filter(
            username=request.data.get("username"),
            email=request.data.get("email"),
        ).exists()
        if username_and_email_exists:
            return Response(request.data, status=status.HTTP_200_OK)
        serializer = AuthSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.create_user(
            serializer.data.get("username"),
            email=serializer.data.get("email"),
        )
        send_mail(
            EMAIL_TITLE.format(serializer.data.get("username")),
            EMAIL_MESSAGE.format(user.password),
            settings.ADMINS_EMAIL,
            [serializer.data.get("email")],
            fail_silently=False,
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


class GetJWTTokenView(views.APIView):
    """
    Класс для получения JWT токена в обмен
    на username и confirmation code.
    """

    def post(self, request):
        serializer = GetJWTTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            User, password=serializer.data.get("confirmation_code")
        )
        refresh = RefreshToken.for_user(user)

        return Response(
            {"token": str(refresh.access_token)},
            status=status.HTTP_201_CREATED,
        )


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserViewSerializer
    permission_classes = (IsAdmin, permissions.IsAuthenticated)
    pagination_class = LimitOffsetPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ("username",)
    lookup_field = "username"

    def update(self, request, *args, **kwargs):
        if request.method in ("PUT"):
            return Response(
                request.data, status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    @action(
        methods=["get", "patch"],
        detail=False,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def me(self, request):
        serializer = self.get_serializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        # если пользователь admin, то можно менять поле role,
        # в остальных случаях нельзя
        if request.user.is_admin:
            serializer.save()
        else:
            serializer.save(role=self.request.user.role)

        return Response(serializer.data, status=status.HTTP_200_OK)

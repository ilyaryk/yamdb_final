from django.urls import include, path
from rest_framework.routers import DefaultRouter
from api.views import (
    AuthSignupView,
    GetJWTTokenView,
    UsersViewSet,
    ReviewViewSet,
    CommentViewSet,
)
from .views import CategoryViewSet, GenreViewSet, TitleViewSet

app_name = "api"

router_v1 = DefaultRouter()
router_v1.register(r"users", UsersViewSet, basename="users")

router_v1.register(r"categories", CategoryViewSet, basename="category")
router_v1.register(r"genres", GenreViewSet, basename="genre")
router_v1.register(r"titles", TitleViewSet, basename="title")
router_v1.register(
    r"titles/(?P<title_id>\d+)/reviews", ReviewViewSet, basename="review"
)

router_v1.register(
    r"titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments",
    CommentViewSet,
    basename="comment",
)

urlpatterns = [
    path("v1/auth/signup/", AuthSignupView.as_view()),
    path("v1/auth/token/", GetJWTTokenView.as_view()),
    path("v1/", include(router_v1.urls)),
]

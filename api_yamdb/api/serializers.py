from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.validators import UniqueValidator

from reviews.models import Category, Title, Genre, GenreTitle, Review, Comment
from users.models import User


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("name", "slug")


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("name", "slug")


class TitleListSerializer(serializers.ModelSerializer):
    genre = GenreSerializer(many=True)
    category = CategorySerializer()
    rating = serializers.IntegerField()

    class Meta:
        fields = "__all__"
        model = Title


class TitleSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=256, required=True)
    year = serializers.IntegerField(required=True)
    genre = serializers.SlugRelatedField(
        required=True,
        slug_field="slug",
        queryset=Genre.objects.all(),
        many=True,
    )
    category = serializers.SlugRelatedField(
        required=True, slug_field="slug", queryset=Category.objects.all()
    )

    class Meta:
        model = Title
        fields = "__all__"

    def create(self, validated_data):
        genres = validated_data.pop("genre")
        title = Title.objects.create(**validated_data)
        for genre in genres:
            GenreTitle.objects.create(genre=genre, title=title)

        return title


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field="username", read_only=True
    )

    class Meta:
        model = Review
        fields = ("id", "text", "author", "score", "pub_date")
        read_only_fields = ("title",)

    def validate(self, data):
        if (
            Review.objects.filter(
                author=self.context.get("request").user,
                title=self.context.get("title_id"),
            ).exists()
            and self.context.get("request").method != "PATCH"
        ):
            raise serializers.ValidationError("Превышен лимит отзывов")
        return data


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field="username", read_only=True
    )

    class Meta:
        model = Comment
        fields = ("id", "text", "author", "pub_date")


class AuthSignupSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        max_length=254,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    username = serializers.RegexField(
        regex=r"^[\w.@+-]+\Z",
        required=True,
        max_length=150,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )

    def validate(self, data):
        if data.get("username") == "me":
            raise serializers.ValidationError("Ошибка: недопустимое имя")

        return data


class GetJWTTokenSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    confirmation_code = serializers.CharField(required=True)

    def validate(self, data):
        if not User.objects.filter(username=data.get("username")).exists():
            raise NotFound("Ошибка: не верный username")
        if not User.objects.filter(
            password=data.get("confirmation_code")
        ).exists():
            raise serializers.ValidationError(
                "Ошибка: не верный confirmation_code"
            )
        return data


class UserViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "bio",
            "role",
        )

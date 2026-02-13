from rest_framework import serializers
from .models import Board


class BoardSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)

    class Meta:
        model = Board
        fields = (
            "id",
            "title",
            "content",
            "author",
            "author_username",
            "created_at",
            "updated_at",
            "view_count",
        )
        read_only_fields = ("id", "author", "created_at", "updated_at", "view_count")


class BoardListSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)

    class Meta:
        model = Board
        fields = ("id", "title", "author_username", "created_at", "view_count")
        read_only_fields = fields

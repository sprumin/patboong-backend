from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Board(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="boards")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    view_count = models.IntegerField(default=0)

    class Meta:
        db_table = "boards"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

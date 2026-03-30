from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Board
from .serializers import BoardSerializer, BoardListSerializer
from .permissions import IsAuthorOrReadOnly


@extend_schema_view(
    list=extend_schema(
        tags=["boards"],
        summary="게시글 목록 조회",
        description="전체 게시글 목록을 조회합니다. 페이지네이션이 적용됩니다.",
    ),
    create=extend_schema(
        tags=["boards"],
        summary="게시글 작성",
        description="새로운 게시글을 작성합니다. 인증이 필요합니다.",
    ),
    retrieve=extend_schema(
        tags=["boards"],
        summary="게시글 상세 조회",
        description="특정 게시글의 상세 정보를 조회합니다. 조회 시 조회수가 1 증가합니다.",
    ),
    update=extend_schema(
        tags=["boards"],
        summary="게시글 전체 수정",
        description="게시글을 전체 수정합니다. 작성자만 수정할 수 있습니다.",
    ),
    partial_update=extend_schema(
        tags=["boards"],
        summary="게시글 부분 수정",
        description="게시글을 부분 수정합니다. 작성자만 수정할 수 있습니다.",
    ),
    destroy=extend_schema(
        tags=["boards"],
        summary="게시글 삭제",
        description="게시글을 삭제합니다. 작성자만 삭제할 수 있습니다.",
    ),
)
class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_serializer_class(self):
        if self.action == "list":
            return BoardListSerializer
        return BoardSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.view_count += 1
        instance.save(update_fields=["view_count"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

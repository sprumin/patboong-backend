from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from django.utils import timezone
from .models import Friendship
from .riot import RIOT_SERVERS, RiotClient

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "main_line",
            "sub_line",
            "tier_top",
            "tier_jungle",
            "tier_mid",
            "tier_adc",
            "tier_support",
            "question",
            "answer",
            "service_terms",
            "privacy_terms",
            "age_terms",
            "marketing_terms",
            "event_terms",
            "riot_game_name",
            "riot_tag_line",
            "riot_server",
            "puuid",
            "verified_at",
            "created_at",
        )
        read_only_fields = ("id", "puuid", "verified_at", "created_at")


class RegisterSerializer(serializers.Serializer):
    user_id = serializers.CharField(required=True)
    user_pw = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        validators=[validate_password],
    )
    email = serializers.EmailField(required=True)
    main_line = serializers.CharField(required=True)
    sub_line = serializers.CharField(required=True)
    tier_top = serializers.CharField(required=True)
    tier_jungle = serializers.CharField(required=True)
    tier_mid = serializers.CharField(required=True)
    tier_adc = serializers.CharField(required=True)
    tier_support = serializers.CharField(required=True)
    question = serializers.CharField(required=True)
    answer = serializers.CharField(required=True)
    service_terms = serializers.BooleanField(required=True)
    privacy_terms = serializers.BooleanField(required=True)
    age_terms = serializers.BooleanField(required=True)
    marketing_terms = serializers.BooleanField(required=False, default=False)
    event_terms = serializers.BooleanField(required=False, default=False)
    riot_game_name = serializers.CharField(required=True, max_length=100)
    riot_tag_line = serializers.CharField(required=True, max_length=50)
    riot_server = serializers.ChoiceField(required=True, choices=RIOT_SERVERS)

    def validate_user_id(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("이미 사용 중인 아이디입니다.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 사용 중인 이메일입니다.")
        return value

    def validate(self, attrs):
        if not attrs.get("service_terms"):
            raise serializers.ValidationError(
                {"service_terms": "서비스 이용약관 동의는 필수입니다."}
            )
        if not attrs.get("privacy_terms"):
            raise serializers.ValidationError(
                {"privacy_terms": "개인정보 수집 동의는 필수입니다."}
            )
        if not attrs.get("age_terms"):
            raise serializers.ValidationError(
                {"age_terms": "만 14세 이상 확인은 필수입니다."}
            )
        account = RiotClient().get_account_by_riot_id(
            attrs["riot_game_name"], attrs["riot_tag_line"], attrs["riot_server"]
        )
        if User.objects.filter(puuid=account["puuid"]).exists():
            raise serializers.ValidationError(
                {"riot_game_name": "This Riot account is already registered."}
            )
        attrs["_riot_account"] = account
        return attrs

    def create(self, validated_data):
        user_id = validated_data.pop("user_id")
        user_pw = validated_data.pop("user_pw")
        riot_account = validated_data.pop("_riot_account")

        try:
            user = User.objects.create_user(
                username=user_id,
                password=user_pw,
                email=validated_data.get("email"),
                main_line=validated_data.get("main_line", ""),
                sub_line=validated_data.get("sub_line", ""),
                tier_top=validated_data.get("tier_top", ""),
                tier_jungle=validated_data.get("tier_jungle", ""),
                tier_mid=validated_data.get("tier_mid", ""),
                tier_adc=validated_data.get("tier_adc", ""),
                tier_support=validated_data.get("tier_support", ""),
                question=validated_data.get("question", ""),
                answer=validated_data.get("answer", ""),
                service_terms=validated_data.get("service_terms", False),
                privacy_terms=validated_data.get("privacy_terms", False),
                age_terms=validated_data.get("age_terms", False),
                marketing_terms=validated_data.get("marketing_terms", False),
                event_terms=validated_data.get("event_terms", False),
                riot_game_name=riot_account.get(
                    "gameName", validated_data["riot_game_name"]
                ),
                riot_tag_line=riot_account.get(
                    "tagLine", validated_data["riot_tag_line"]
                ),
                riot_server=validated_data["riot_server"],
                puuid=riot_account["puuid"],
                verified_at=timezone.now(),
            )
        except IntegrityError:
            raise serializers.ValidationError(
                {"user_id": "이미 사용 중인 아이디입니다."}
            )
        return user


class LoginSerializer(serializers.Serializer):
    user_id = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class ProfileUpdateSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(source="username", required=False)
    user_pw = serializers.CharField(
        source="password",
        write_only=True,
        required=False,
        validators=[validate_password],
    )
    riot_server = serializers.ChoiceField(required=False, choices=RIOT_SERVERS)

    class Meta:
        model = User
        fields = (
            "user_id",
            "user_pw",
            "email",
            "main_line",
            "sub_line",
            "tier_top",
            "tier_jungle",
            "tier_mid",
            "tier_adc",
            "tier_support",
            "question",
            "answer",
            "service_terms",
            "privacy_terms",
            "age_terms",
            "marketing_terms",
            "event_terms",
            "riot_game_name",
            "riot_tag_line",
            "riot_server",
        )
        extra_kwargs = {
            "riot_game_name": {"required": False},
            "riot_tag_line": {"required": False},
        }

    def validate_username(self, value):
        if User.objects.exclude(pk=self.instance.pk).filter(username=value).exists():
            raise serializers.ValidationError("This user ID is already in use.")
        return value

    def validate_email(self, value):
        if User.objects.exclude(pk=self.instance.pk).filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def validate(self, attrs):
        riot_fields = ("riot_game_name", "riot_tag_line", "riot_server")
        riot_changed = any(
            field in attrs and attrs[field] != getattr(self.instance, field)
            for field in riot_fields
        )
        if riot_changed:
            values = {
                field: attrs.get(field, getattr(self.instance, field))
                for field in riot_fields
            }
            if not all(values.values()):
                raise serializers.ValidationError(
                    {"riot_game_name": "All Riot ID fields are required."}
                )
            account = RiotClient().get_account_by_riot_id(
                values["riot_game_name"],
                values["riot_tag_line"],
                values["riot_server"],
            )
            if (
                User.objects.exclude(pk=self.instance.pk)
                .filter(puuid=account["puuid"])
                .exists()
            ):
                raise serializers.ValidationError(
                    {"riot_game_name": "This Riot account is already registered."}
                )
            attrs["_riot_account"] = account
        return attrs

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        riot_account = validated_data.pop("_riot_account", None)
        if riot_account:
            validated_data["riot_game_name"] = riot_account.get(
                "gameName", validated_data.get("riot_game_name", instance.riot_game_name)
            )
            validated_data["riot_tag_line"] = riot_account.get(
                "tagLine", validated_data.get("riot_tag_line", instance.riot_tag_line)
            )
            validated_data["puuid"] = riot_account["puuid"]
            validated_data["verified_at"] = timezone.now()
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save(update_fields=["password"])
        return instance


class FriendProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "main_line",
            "sub_line",
            "tier_top",
            "tier_jungle",
            "tier_mid",
            "tier_adc",
            "tier_support",
            "riot_game_name",
            "riot_tag_line",
            "riot_server",
            "puuid",
            "verified_at",
        )


class FriendAddSerializer(serializers.Serializer):
    riot_game_name = serializers.CharField(required=True, max_length=100)
    riot_tag_line = serializers.CharField(required=True, max_length=50)
    riot_server = serializers.ChoiceField(required=True, choices=RIOT_SERVERS)

    def create(self, validated_data):
        account = RiotClient().get_account_by_riot_id(
            validated_data["riot_game_name"],
            validated_data["riot_tag_line"],
            validated_data["riot_server"],
        )
        try:
            friend = User.objects.get(puuid=account["puuid"])
        except User.DoesNotExist as exc:
            raise serializers.ValidationError(
                {"detail": "No registered user matches this Riot ID."}
            ) from exc

        user = self.context["request"].user
        if friend == user:
            raise serializers.ValidationError(
                {"detail": "You cannot add yourself as a friend."}
            )
        with transaction.atomic():
            friendship, created = Friendship.objects.get_or_create(
                user=user, friend=friend
            )
            if not created:
                raise serializers.ValidationError(
                    {"detail": "This user is already your friend."}
                )
        return friendship

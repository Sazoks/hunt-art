from typing import (
    Any,
    Optional,
)

from django.apps import apps
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager as DefaultUserManager

import apps.users.models as models


class UserManager(DefaultUserManager):
    """Класс для управления пользователями"""

    def _create_user(
        self,
        username: str,
        password: str,
        **extra_fields,
    ) -> 'models.User':
        """Создание пользователя с юзернеймом и паролем"""

        if not username:
            raise ValueError("The given username must be set")

        # Lookup the real model class from the global app registry so this
        # manager method can be used in migrations. This is fine because
        # managers are by definition working on the real model.
        GlobalUserModel = apps.get_model(
            self.model._meta.app_label, self.model._meta.object_name
        )
        username = GlobalUserModel.normalize_username(username)
        user = self.model(username=username, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)

        return user
    
    def _create_profile_for(self, user: 'models.User') -> 'models.UserProfile':
        return models.UserProfile.objects.create(user=user)

    def create_user(
        self,
        username: str,
        password: str | None = None,
        with_profile: bool = True,
        **extra_fields,
    ) -> 'models.User':
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user = self._create_user(username, password, **extra_fields)
        if with_profile:
            self._create_profile_for(user)

        return user

    def create_superuser(
        self,
        username: str,
        password: str | None = None,
        **extra_fields,
    ) -> 'models.User':
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(username, password, **extra_fields)
    
    def get_user_by_pk(self, pk: Any, with_profile: bool = True) -> Optional['models.User']:
        queryset = models.User.objects.filter(pk=pk)
        if with_profile:
            queryset = queryset.select_related('profile')

        return queryset.first()
    
    def exists(self, pk: Any) -> bool:
        return models.User.objects.filter(pk=pk).exists()
    
    def add_subscription(self, subscriber_pk: Any, other_user_pk: Any) -> None:
        model_name = models.User._meta.model_name
        new_subscription_data = {
            f'from_{model_name}_id': subscriber_pk,
            f'to_{model_name}_id': other_user_pk,
        }
        models.User.subscriptions.through.objects.create(**new_subscription_data)

    def remove_subscription(self, subscriber_pk: Any, other_user_pk: Any) -> None:        
        model_name = models.User._meta.model_name
        subscription_info = {
            f'from_{model_name}_id': subscriber_pk,
            f'to_{model_name}_id': other_user_pk,
        }
        models.User.subscriptions.through.objects.filter(**subscription_info).delete()

    def user_is_follower_other_user(self, user_pk: Any, other_user_pk: Any) -> bool:
        model_name = models.User._meta.model_name
        subscription_info = {
            f'from_{model_name}_id': user_pk,
            f'to_{model_name}_id': other_user_pk,
        }
        return models.User.subscriptions.through.objects.filter(**subscription_info).exists()

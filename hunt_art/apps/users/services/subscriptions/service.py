from apps.users.models import User

from . import exceptions


class UserSubscriptionsService:
    def __init__(self, current_user: User) -> None:
        self.__current_user = current_user

    def subscribe_to_user(self, other_user: User) -> None:
        if User.objects.user_is_follower_other_user(
            user_pk=self.__current_user.pk,
            other_user_pk=other_user.pk,
        ):
            raise exceptions.UserIsAlreadyFollower(self.__current_user, other_user)
        
        User.objects.add_subscription(
            subscriber_pk=self.__current_user.pk,
            other_user_pk=other_user.pk,
        )

    def unsubscribe_from_user(self, other_user: User) -> None:
        if not User.objects.user_is_follower_other_user(
            user_pk=self.__current_user.pk,
            other_user_pk=other_user.pk,
        ):
            raise exceptions.UserIsNotFollower(self.__current_user, other_user)

        User.objects.remove_subscription(
            subscriber_pk=self.__current_user.pk,
            other_user_pk=other_user.pk,
        )

    def remove_from_subscribers(self, other_user: User) -> None:
        if not User.objects.user_is_follower_other_user(
            user_pk=other_user.pk,
            other_user_pk=self.__current_user.pk,
        ):
            raise exceptions.UserIsNotFollower(other_user, self.__current_user)

        User.objects.remove_subscription(
            subscriber_pk=other_user.pk,
            other_user_pk=self.__current_user.pk,
        )

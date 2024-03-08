from apps.users.models import User


class UserIsAlreadyFollower(Exception):
    def __init__(self, current_user: User, other_user: User) -> None:
        self.message = (
            f'Пользователь {current_user} уже является подписчиком '
            f'пользователя {other_user}.'
        )
        super().__init__(self.message)


class UserIsNotFollower(Exception):
    def __init__(self, current_user: User, other_user: User) -> None:
        self.message = (
            f'Пользователь {current_user} не является подписчиком '
            f'пользователя {other_user}.'
        )
        super().__init__(self.message)

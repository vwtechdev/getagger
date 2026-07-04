from django.contrib.auth.backends import ModelBackend


class AllowInactiveBackend(ModelBackend):
    """Permite autenticação de usuários inativos.
    A verificação de ``is_active`` é feita na ``LoginView.form_valid``,
    que redireciona para ``pending_approval`` se inativo.
    """
    def user_can_authenticate(self, user):
        return True

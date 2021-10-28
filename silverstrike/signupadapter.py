from allauth.account.adapter import DefaultAccountAdapter


class SignupDisabledAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False

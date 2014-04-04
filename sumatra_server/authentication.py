"""
Authentication handler for using django.contrib.auth

Based on http://yml-blog.blogspot.com/2009/10/django-piston-authentication-against.html
"""

from django.conf import settings
from django.utils.http import urlquote
from django.http import HttpResponseRedirect
from sumatra_server.resource import determine_emitter


class DjangoAuthentication(object):
    """
    Django authentication.
    """

    def __init__(self, login_url=None, redirect_field_name="next"):
        if not login_url:
            login_url = settings.LOGIN_URL
        self.login_url = login_url
        self.redirect_field_name = redirect_field_name
        self.next = "/"  # should use settings.LOGIN_REDIRECT_URL if defined

    def is_authenticated(self, request):
        self.next = urlquote(request.get_full_path())
        return request.user.is_authenticated()

    def challenge(self):
        """
        Redirect to the login page.
        """
        return HttpResponseRedirect('%s?%s=%s' % (
            self.login_url, self.redirect_field_name, self.next))


class AuthenticationDispatcher(object):

    def __init__(self, authenticator_map, default):
        """
        authenticator_map should be something like:
        { "html": "DjangoAuthentication" }
        """
        self.authenticator_map = authenticator_map
        self.default_authenticator = default

    def is_authenticated(self, request):
        session = request.session.session_key
        if session:
            self.current_authenticator = DjangoAuthentication()
        else:
            em = determine_emitter(request)
            if em in self.authenticator_map:
                self.current_authenticator = self.authenticator_map[em]
            else:
                self.current_authenticator = self.default_authenticator
        return self.current_authenticator.is_authenticated(request)

    def challenge(self):
        return self.current_authenticator.challenge()

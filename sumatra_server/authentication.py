"""
Authentication handler for using django.contrib.auth

Based on http://yml-blog.blogspot.com/2009/10/django-piston-authentication-against.html


:copyright: Copyright 2010-2015 Andrew Davison
:license: BSD 2-clause, see COPYING for details.
"""

import binascii
import base64
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth import authenticate
from django.contrib.auth.models import AnonymousUser
from django.utils.http import urlquote
from django.http import HttpResponseRedirect


class HttpBasicAuthentication(object):
    # based on the Django Piston package

    def is_authenticated(self, request):
        auth_string = request.META.get('HTTP_AUTHORIZATION', None)
        if not auth_string:
            return False
        try:
            (authmeth, auth) = auth_string.split(" ", 1)
            if not authmeth.lower() == 'basic':
                return False

            auth = base64.b64decode(auth.strip()).decode('utf-8')
            username, password = auth.split(':', 1)
        except (ValueError, binascii.Error):
            return False
        request.user = authenticate(username=username, password=password) or AnonymousUser()
        return request.user not in (False, None, AnonymousUser())

    def challenge(self):
        resp = HttpResponse("Authorization Required")
        resp['WWW-Authenticate'] = 'Basic realm="Sumatra Server API"'
        resp.status_code = 401
        return resp

    def __repr__(self):
        return u'<HTTPBasic: realm=Sumatra Server API>'


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
        return request.user.is_authenticated

    def challenge(self):
        """
        Redirect to the login page.
        """
        return HttpResponseRedirect('%s?%s=%s' % (
            self.login_url, self.redirect_field_name, self.next))


class AuthenticationDispatcher(object):

    def is_authenticated(self, request):
        session = request.session.session_key
        if session:
            self.current_authenticator = DjangoAuthentication()
        else:
            self.current_authenticator = HttpBasicAuthentication()
        return self.current_authenticator.is_authenticated(request)

    def challenge(self):
        return self.current_authenticator.challenge()

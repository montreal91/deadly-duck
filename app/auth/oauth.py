
"""
This file contains OAuth-related middleware.

Created on Aug 25, 2018

@author: montreal91
"""

import json

import requests

from typing import Any
from typing import Dict
from typing import Optional

from flask import current_app
from flask import redirect
from flask import request
from flask import Response
from flask import url_for
from rauth import OAuth2Service


class DdOAuthSignIn:
    providers: Optional[Dict[str, Any]] = None

    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name
        credentials = current_app.config["OAUTH_CREDENTIALS"][provider_name]
        self.consumer_id = credentials["id"]
        self.consumer_secret = credentials["secret"]


    def Authorize(self) -> None:
        pass


    def Callback(self) -> tuple:
        pass


    def GetCallbackUrl(self) -> str:
        return url_for(
            "auth.OauthCallback",
            provider=self.provider_name,
            _external=True,
        )


    @classmethod
    def GetProvider(cls, provider_name: str):
        if cls.providers is None:
            cls.providers = {}
            for provider_class in cls.__subclasses__():
                provider = provider_class()
                cls.providers[provider.provider_name] = provider
        return cls.providers[provider_name]


class DdGoogleSignIn(DdOAuthSignIn):
    def __init__(self):
        super().__init__("google")
        self.service = OAuth2Service(
            name="google",
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
            access_token_url="https://www.googleapis.com/oauth2/v4/token",
        )
        self.sign_in_url = "https://www.googleapis.com/oauth2/v1/userinfo"


    def Authorize(self) -> Response:
        return redirect(
            self.service.get_authorize_url(
                scope="profile",
                response_type="code",
                redirect_uri=self.GetCallbackUrl(),
            )
        )


    def Callback(self) -> tuple:
        if "code" not in request.args:
            return None, None, None

        payload = {
            "client_id": self.consumer_id,
            "client_secret": self.consumer_secret,
            "redirect_uri": self.GetCallbackUrl(),
            "code": request.args["code"],
            "grant_type": "authorization_code"
        }

        resp = requests.post(
            self.service.access_token_url,
            data=payload
        ).json()

        me = requests.get(
            self.sign_in_url,
            params={
                "alt": "json",
                "access_token": resp["access_token"]
            },
            cookies=dict(request.cookies)
        ).json()

        return (
            "google${}".format(me["id"]),
            "{initial}{family_name}".format(
                initial=me.get("given_name")[0].lower(),
                family_name=me.get("family_name").lower()
            ),
            None
        )


class DdVkSignIn(DdOAuthSignIn):
    def __init__(self):
        super().__init__("vk")
        self.service = OAuth2Service(
            name="vk",
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url="https://oauth.vk.com/authorize",
            access_token_url="https://oauth.vk.com/access_token",
            base_url="https://oauth.vk.com/"
        )


    def Authorize(self) -> Response:
        return redirect(
            self.service.get_authorize_url(
                scope="email",
                response_type="code",
                redirect_uri=self.GetCallbackUrl()
            )
        )

    def Callback(self) -> tuple:
        if "code" not in request.args:
            return None, None, None

        payload = {
            "client_id": self.consumer_id,
            "client_secret": self.consumer_secret,
            "redirect_uri": self.GetCallbackUrl(),
            "code": request.args["code"]
        }
        me = requests.get(
            self.service.access_token_url,
            cookies=dict(request.cookies),
            params=payload
        ).json()
        return (
            "vk${0:d}".format(me["user_id"]),
            me.get("email").split("@")[0],
            me.get("email")
        )

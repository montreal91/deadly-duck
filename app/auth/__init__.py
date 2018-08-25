
from flask import Blueprint

from app.data.main.main_service import DdMainService


auth = Blueprint( "auth", __name__ )
auth.main_service = DdMainService()


from app.auth import views


from datetime import datetime

from sqlalchemy import and_
from sqlalchemy import text

from app import db
from app.custom_queries import INCOMING_MESSAGES_SQL
from app.custom_queries import NUMBER_OF_TOTAL_INCOMING_NEW_MESSAGES


class DdMessage(db.Model):
    __tablename__ = "messages"
    pk = db.Column(db.Integer, primary_key=True)

    from_pk = db.Column(db.Integer, db.ForeignKey("users.pk"))
    to_pk = db.Column(db.Integer, db.ForeignKey("users.pk"))

    subject_c = db.Column(db.String(64))
    text_txt = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)

    timestamp_dt = db.Column(db.DateTime, default=datetime.utcnow())

    from_user = db.relationship("DdUser", foreign_keys=[from_pk])
    to_user = db.relationship("DdUser", foreign_keys=[to_pk])

    def __repr__(self):
        return "<DdMessage #{pk:d} from {username1:s} to {username2:s}".format(
            pk=self.pk,
            username1=self.from_user.username,
            username2=self.to_user.username
        )


class DdDaoMessage(object):
    def CreateMessage(self, from_pk=0, to_pk=0, subject="", text=""):
        msg = DdMessage()
        msg.from_pk = from_pk
        msg.to_pk = to_pk
        msg.subject_c = subject
        msg.text_txt = text

        return msg

    def GetAllMessagesFromUserToUser(self, from_pk=0, to_pk=0):
        return DdMessage.query.filter(and_(DdMessage.from_pk == from_pk, DdMessage.to_pk == to_pk)).all()

    def GetAllIncomingMessages(self, user_pk=0):
        return DdMessage.query.from_statement(
            text(INCOMING_MESSAGES_SQL).params(user_pk=user_pk)
        ).all()

    def GetAllOutcomingMessages(self, user_pk=0):
        return DdMessage.query.filter_by(from_pk=user_pk).order_by(DdMessage.timestamp_dt.desc()).all()

    def GetMessageByPk(self, pk):
        return DdMessage.query.get_or_404(pk)

    def GetTotalNumberOfIncomingNewMessages(self, user_pk=0):
        query_res = db.engine.execute(
            text(NUMBER_OF_TOTAL_INCOMING_NEW_MESSAGES).params(
                user_pk=user_pk
            )
        ).first()
        return query_res["number_of_incoming_messages"]

    def SaveMessage(self, message=None):
        db.session.add(message)
        db.session.commit()

    def SaveMessages(self, messages=[]):
        db.session.add_all(messages)
        db.session.commit()

"""added friendship

Revision ID: 3d2ead055f0
Revises: 2a64801f6e6
Create Date: 2017-03-18 05:15:43.477758

"""

# revision identifiers, used by Alembic.
revision = '3d2ead055f0'
down_revision = '2a64801f6e6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('friend_requests',
    sa.Column('pk', sa.Integer(), nullable=False),
    sa.Column('from_pk', sa.Integer(), nullable=True),
    sa.Column('to_pk', sa.Integer(), nullable=True),
    sa.Column('timestamp_dt', sa.DateTime(), nullable=True),
    sa.Column('is_accepted', sa.Boolean(), nullable=True),
    sa.Column('is_rejected', sa.Boolean(), nullable=True),
    sa.Column('message_txt', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['from_pk'], ['users.pk'], ),
    sa.ForeignKeyConstraint(['to_pk'], ['users.pk'], ),
    sa.PrimaryKeyConstraint('pk')
    )
    op.create_table('friendship',
    sa.Column('pk', sa.Integer(), nullable=False),
    sa.Column('friend_one_pk', sa.Integer(), nullable=True),
    sa.Column('friend_two_pk', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('timestamp_dt', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['friend_one_pk'], ['users.pk'], ),
    sa.ForeignKeyConstraint(['friend_two_pk'], ['users.pk'], ),
    sa.PrimaryKeyConstraint('pk')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('friendship')
    op.drop_table('friend_requests')
    ### end Alembic commands ###

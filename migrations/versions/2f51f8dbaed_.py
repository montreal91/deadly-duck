"""empty message

Revision ID: 2f51f8dbaed
Revises: 47a03b99c38
Create Date: 2018-08-25 18:30:54.802650

"""

# revision identifiers, used by Alembic.
revision = '2f51f8dbaed'
down_revision = '47a03b99c38'

from random import randint

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column(
        'social_pk',
        sa.String(length=64),
        nullable=False,
        server_default=str(randint(0, 10 ** 20))
    ))
    op.drop_index('ix_users_email', table_name='users')
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.drop_index('ix_users_username', table_name='users')
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)
    op.create_unique_constraint(None, 'users', ['social_pk'])
    op.drop_column('users', 'confirmed')
    op.drop_column('users', 'password_hash')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('password_hash', sa.VARCHAR(length=128), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('confirmed', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'users', type_='unique')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.drop_column('users', 'social_pk')
    ### end Alembic commands ###
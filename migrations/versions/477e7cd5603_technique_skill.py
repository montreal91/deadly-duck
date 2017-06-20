"""technique skill

Revision ID: 477e7cd5603
Revises: 5365aa2eacd
Create Date: 2017-06-20 15:24:31.947388

"""

# revision identifiers, used by Alembic.
revision = '477e7cd5603'
down_revision = '5365aa2eacd'

from random import randint, choice

from alembic import op
import sqlalchemy as sa

DdBase = sa.ext.declarative.declarative_base()

class DdPlayerHelper(DdBase):
    __tablename__ = 'players'
    __table_args__ = {'extend_existing': True}
    pk_n = sa.Column(sa.Integer, primary_key=True)
    technique_n = sa.Column(sa.Numeric(5,2))
    technique_pk = sa.Column(
        sa.Integer,
        sa.ForeignKey('skills.pk'),
        nullable=False
    )

def upgrade():
    with op.batch_alter_table('players') as bop:
        bop.add_column(
            sa.Column('technique_pk', sa.Integer(), nullable=True)
        )
        bop.create_foreign_key(
            "technique_fk_constraint",
            'skills',
            ['technique_pk'],
            ['pk']
        )

    connection = op.get_bind()
    Session = sa.orm.sessionmaker(bind=connection)
    session = Session()
    skills = sa.Table(
        'skills',
        sa.MetaData(),
        autoload=True,
        autoload_with=connection
    )
    ind = session.query(sa.func.max(skills.columns['pk'])).first()[0] + 1
    for row in session.query(DdPlayerHelper).all():
        absmax = int(float(row.technique_n) * 10)
        curmax = int(round(absmax / randint(2,4)))
        talent = choice([1, 2, 4])
        connection.execute(
            skills.insert().values(
                pk = ind,
                absolute_maximum_n=absmax,
                current_maximum_n=curmax,
                current_value_n=curmax,
                talent_n=talent,
                experience_n=0
            )
        )
        session.query(DdPlayerHelper).filter_by(pk_n=row.pk_n).update(
            {'technique_pk': ind}
        )
        ind += 1

    with op.batch_alter_table('players') as bop:
        bop.drop_column('technique_n')


def downgrade():
    op.add_column('players', sa.Column('technique_n', sa.NUMERIC(precision=5, scale=2), nullable=False))
    connection = op.get_bind()
    skills = sa.Table(
        'skills',
        sa.MetaData(),
        autoload=True,
        autoload_with=connection
    )
    Session = sa.orm.sessionmaker(bind=connection)
    session = Session()
    for row in connection.execute(skills.select()):
        session.query(DdPlayerHelper).filter_by(technique_pk=row.pk).update(
            {
                'technique_n': round(row.absolute_maximum_n / 10, 2),
            }
        )
    with op.batch_alter_table('players') as bop:
        bop.drop_constraint(None, type_='foreignkey')
        bop.drop_column('technique_pk')
    ### end Alembic commands ###

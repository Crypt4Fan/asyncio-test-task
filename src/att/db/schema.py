import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


CORE_SCHEMA = 'core'

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = sa.MetaData(
    schema=CORE_SCHEMA,
    naming_convention=convention
)

t_user = sa.Table(
    'user', metadata,
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              server_default=sa.func.gen_random_uuid()),
    sa.Column('login', sa.String, nullable=False),
    sa.Column('password', sa.String, nullable=False),
    sa.CheckConstraint('length(login) > 0', name='login_len_gt_0'),
    sa.CheckConstraint('lower(login) = login', name='login_is_lowercase'),
    sa.CheckConstraint('length(password) > 0', name='password_len_gt_0'),
)

t_group = sa.Table(
    'group', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('name', sa.String, nullable=False),
    sa.CheckConstraint('length(name) > 0', name='group_name_len_gt_0'),
    sa.CheckConstraint('lower(name) = name', name='group_name_is_lowercase'),
    sa.UniqueConstraint('name')
)

t_user_group = sa.Table(
    'user_group', metadata,
    sa.Column('user_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
    sa.Column('group_id', sa.Integer,
              sa.ForeignKey('group.id', ondelete='CASCADE'), nullable=False),
    sa.UniqueConstraint('user_id', 'group_id')
)

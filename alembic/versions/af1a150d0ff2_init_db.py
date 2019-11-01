"""init db

Revision ID: af1a150d0ff2
Revises:
Create Date: 2019-07-08 21:54:35.108279

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'af1a150d0ff2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE SCHEMA "core"')
    user_table = op.create_table('user',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('login', sa.String(), nullable=False),
        sa.Column('password', sa.String(), nullable=False),
        sa.CheckConstraint('length(login) > 0', name=op.f('ck_user_login_len_gt_0')),
        sa.CheckConstraint('length(password) > 0', name=op.f('ck_user_password_len_gt_0')),
        sa.CheckConstraint('lower(login) = login', name=op.f('ck_user_login_is_lowercase')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_user')),
        schema='core'
    )
    op.execute(
        user_table.insert().values([
            {'login': 'bob', 'password': sa.func.crypt('secret', sa.func.gen_salt('bf', 8))},
            {'login': 'randy', 'password': sa.func.crypt('god', sa.func.gen_salt('bf', 8))},
            {'login': 'john', 'password': sa.func.crypt('password', sa.func.gen_salt('bf', 8))},
        ])
    )


def downgrade():
    op.drop_table('user', schema='core')
    op.execute('DROP SCHEMA "core"')

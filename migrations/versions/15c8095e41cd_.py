"""empty message

Revision ID: 15c8095e41cd
Revises: 63fe58e770d1
Create Date: 2019-07-17 09:28:18.502124

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '15c8095e41cd'
down_revision = '63fe58e770d1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('download_error', sa.Column('last_tweeted_at', sa.DateTime(), nullable=True))
    op.add_column('validation_error', sa.Column('last_tweeted_at', sa.DateTime(), nullable=True))
    op.add_column('xml_error', sa.Column('last_tweeted_at', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('xml_error', 'last_tweeted_at')
    op.drop_column('validation_error', 'last_tweeted_at')
    op.drop_column('download_error', 'last_tweeted_at')
    # ### end Alembic commands ###
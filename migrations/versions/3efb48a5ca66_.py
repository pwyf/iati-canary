"""empty message

Revision ID: 3efb48a5ca66
Revises: 
Create Date: 2019-04-09 22:37:36.303949

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3efb48a5ca66'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('publisher',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('total_datasets', sa.Integer(), nullable=False),
    sa.Column('first_published_on', sa.Date(), nullable=True),
    sa.Column('last_checked_at', sa.DateTime(), nullable=True),
    sa.Column('queued_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('contact',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('email', sa.Text(), nullable=False),
    sa.Column('publisher_id', sa.String(length=255), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('confirmed_at', sa.DateTime(), nullable=True),
    sa.Column('last_messaged_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['publisher_id'], ['publisher.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email', 'publisher_id')
    )
    op.create_table('dataseterror',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('dataset_id', sa.String(length=255), nullable=False),
    sa.Column('dataset_name', sa.Text(), nullable=False),
    sa.Column('dataset_url', sa.String(length=255), nullable=False),
    sa.Column('publisher_id', sa.String(length=255), nullable=False),
    sa.Column('error_type', sa.String(length=20), nullable=True),
    sa.Column('last_status', sa.String(length=20), nullable=False),
    sa.Column('error_count', sa.Integer(), nullable=False),
    sa.Column('check_count', sa.Integer(), nullable=False),
    sa.Column('last_errored_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['publisher_id'], ['publisher.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('dataset_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('dataseterror')
    op.drop_table('contact')
    op.drop_table('publisher')
    # ### end Alembic commands ###
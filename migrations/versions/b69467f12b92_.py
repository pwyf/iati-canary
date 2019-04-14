"""empty message

Revision ID: b69467f12b92
Revises: 3efb48a5ca66
Create Date: 2019-04-14 21:31:40.175088

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b69467f12b92'
down_revision = '3efb48a5ca66'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('download_error',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('dataset_id', sa.String(length=255), nullable=False),
    sa.Column('dataset_name', sa.Text(), nullable=True),
    sa.Column('dataset_url', sa.String(length=255), nullable=False),
    sa.Column('currently_erroring', sa.Boolean(), nullable=False),
    sa.Column('error_count', sa.Integer(), nullable=False),
    sa.Column('check_count', sa.Integer(), nullable=False),
    sa.Column('last_errored_at', sa.DateTime(), nullable=False),
    sa.Column('publisher_id', sa.String(length=255), nullable=False),
    sa.ForeignKeyConstraint(['publisher_id'], ['publisher.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('dataset_id')
    )
    op.create_table('validation_error',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('dataset_id', sa.String(length=255), nullable=False),
    sa.Column('dataset_name', sa.Text(), nullable=True),
    sa.Column('dataset_url', sa.String(length=255), nullable=False),
    sa.Column('currently_erroring', sa.Boolean(), nullable=False),
    sa.Column('error_count', sa.Integer(), nullable=False),
    sa.Column('check_count', sa.Integer(), nullable=False),
    sa.Column('last_errored_at', sa.DateTime(), nullable=False),
    sa.Column('publisher_id', sa.String(length=255), nullable=False),
    sa.ForeignKeyConstraint(['publisher_id'], ['publisher.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('dataset_id')
    )
    op.create_table('xml_error',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('dataset_id', sa.String(length=255), nullable=False),
    sa.Column('dataset_name', sa.Text(), nullable=True),
    sa.Column('dataset_url', sa.String(length=255), nullable=False),
    sa.Column('currently_erroring', sa.Boolean(), nullable=False),
    sa.Column('error_count', sa.Integer(), nullable=False),
    sa.Column('check_count', sa.Integer(), nullable=False),
    sa.Column('last_errored_at', sa.DateTime(), nullable=False),
    sa.Column('publisher_id', sa.String(length=255), nullable=False),
    sa.ForeignKeyConstraint(['publisher_id'], ['publisher.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('dataset_id')
    )
    op.drop_table('dataseterror')
    op.drop_column('publisher', 'queued_at')
    op.drop_column('publisher', 'last_checked_at')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('publisher', sa.Column('last_checked_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.add_column('publisher', sa.Column('queued_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.create_table('dataseterror',
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('modified_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('dataset_id', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('dataset_name', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('dataset_url', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('publisher_id', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('error_type', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('last_status', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.Column('error_count', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('check_count', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('last_errored_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['publisher_id'], ['publisher.id'], name='dataseterror_publisher_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='dataseterror_pkey'),
    sa.UniqueConstraint('dataset_id', name='dataseterror_dataset_id_key')
    )
    op.drop_table('xml_error')
    op.drop_table('validation_error')
    op.drop_table('download_error')
    # ### end Alembic commands ###

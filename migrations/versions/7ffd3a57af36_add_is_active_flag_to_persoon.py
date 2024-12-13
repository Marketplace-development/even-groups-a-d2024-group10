def upgrade():
    # ### Create 'bericht' table ###
    op.create_table(
        'bericht',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('afzender_id', sa.String(length=10), nullable=False),
        sa.Column('ontvanger_id', sa.String(length=10), nullable=False),
        sa.Column('klusnummer', sa.String(length=36), nullable=True),
        sa.Column('inhoud', sa.Text(), nullable=False),
        sa.Column('verzonden_op', sa.TIMESTAMP(), nullable=False),
        sa.ForeignKeyConstraint(['afzender_id'], ['persoon.idnummer']),
        sa.ForeignKeyConstraint(['klusnummer'], ['klus.klusnummer']),
        sa.ForeignKeyConstraint(['ontvanger_id'], ['persoon.idnummer']),
        sa.PrimaryKeyConstraint('id'),
    )

    # ### Modify 'klus' table ###
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.alter_column('categorie', existing_type=sa.VARCHAR(length=50), nullable=True)
        batch_op.alter_column('locatie', existing_type=sa.VARCHAR(length=100), nullable=True)
        batch_op.alter_column('beschrijving', existing_type=sa.TEXT(), nullable=True)
        batch_op.alter_column('vergoeding', existing_type=sa.NUMERIC(precision=10, scale=2), nullable=True)
        batch_op.alter_column('status', existing_type=sa.VARCHAR(length=20), nullable=True)
        batch_op.drop_constraint('klus_categorie_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'categorie', ['categorie'], ['categorie'], ondelete='SET NULL')
        batch_op.drop_column('voltooid_op')

    # ### Modify 'persoon' table ###
    with op.batch_alter_table('persoon', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active_flag', sa.Boolean(), nullable=True))

    # ### Modify 'rating' table ###
    with op.batch_alter_table('rating', schema=None) as batch_op:
        # Add non-nullable columns with server defaults
        batch_op.add_column(sa.Column('communicatie', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('algemene_ervaring', sa.Integer(), nullable=False, server_default='0'))
        # Remove server defaults after column creation
        batch_op.alter_column('communicatie', server_default=None)
        batch_op.alter_column('algemene_ervaring', server_default=None)
        
        # Adjust existing columns
        batch_op.alter_column('kluszoeker_id', existing_type=sa.VARCHAR(length=10), nullable=False)
        batch_op.alter_column('klusaanbieder_id', existing_type=sa.VARCHAR(length=10), nullable=False)
        batch_op.alter_column('betrouwbaarheid', existing_type=sa.INTEGER(), nullable=False)
        batch_op.alter_column('tijdigheid', existing_type=sa.INTEGER(), nullable=False)
        batch_op.alter_column('kwaliteit', existing_type=sa.INTEGER(), nullable=False)
        
        # Drop constraints and unused columns
        batch_op.drop_constraint('unique_aanbieder_rating', type_='unique')
        batch_op.drop_constraint('unique_zoeker_rating', type_='unique')
        batch_op.drop_column('vriendelijkheid_aanbieder')
        batch_op.drop_column('communicatie_aanbieder')
        batch_op.drop_column('gastvrijheid')
        batch_op.drop_column('vriendelijkheid_zoeker')
        batch_op.drop_column('communicatie_zoeker')
        batch_op.drop_column('algemene_ervaring_zoeker')
        batch_op.drop_column('algemene_ervaring_aanbieder')


def downgrade():
    # Reverse modifications in 'rating' table
    with op.batch_alter_table('rating', schema=None) as batch_op:
        batch_op.add_column(sa.Column('algemene_ervaring_aanbieder', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('algemene_ervaring_zoeker', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('communicatie_zoeker', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('vriendelijkheid_zoeker', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('gastvrijheid', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('communicatie_aanbieder', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('vriendelijkheid_aanbieder', sa.INTEGER(), nullable=True))
        batch_op.create_unique_constraint('unique_zoeker_rating', ['klusnummer', 'kluszoeker_id', 'klusaanbieder_id', 'vriendelijkheid_zoeker'])
        batch_op.create_unique_constraint('unique_aanbieder_rating', ['klusnummer', 'kluszoeker_id', 'klusaanbieder_id', 'vriendelijkheid_aanbieder'])
        batch_op.alter_column('kwaliteit', existing_type=sa.INTEGER(), nullable=True)
        batch_op.alter_column('tijdigheid', existing_type=sa.INTEGER(), nullable=True)
        batch_op.alter_column('betrouwbaarheid', existing_type=sa.INTEGER(), nullable=True)
        batch_op.alter_column('klusaanbieder_id', existing_type=sa.VARCHAR(length=10), nullable=True)
        batch_op.alter_column('kluszoeker_id', existing_type=sa.VARCHAR(length=10), nullable=True)
        batch_op.drop_column('algemene_ervaring')
        batch_op.drop_column('communicatie')

    # Reverse modifications in 'persoon' table
    with op.batch_alter_table('persoon', schema=None) as batch_op:
        batch_op.drop_column('is_active_flag')

    # Reverse modifications in 'klus' table
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.add_column(sa.Column('voltooid_op', postgresql.TIMESTAMP(), nullable=True))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('klus_categorie_fkey', 'categorie', ['categorie'], ['categorie'])
        batch_op.alter_column('status', existing_type=sa.VARCHAR(length=20), nullable=False)
        batch_op.alter_column('vergoeding', existing_type=sa.NUMERIC(precision=10, scale=2), nullable=False)
        batch_op.alter_column('beschrijving', existing_type=sa.TEXT(), nullable=False)
        batch_op.alter_column('locatie', existing_type=sa.VARCHAR(length=100), nullable=False)
        batch_op.alter_column('categorie', existing_type=sa.VARCHAR(length=50), nullable=False)

    # Drop 'bericht' table
    op.drop_table('bericht')

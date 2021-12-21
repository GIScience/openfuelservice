"""Add wikipedia and carfueldata models

Revision ID: 73883d2da3d5
Revises: 387742d55298
Create Date: 2021-12-21 00:21:38.844394

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "73883d2da3d5"
down_revision = "387742d55298"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "carfueldatacar",
        sa.Column("id", sa.CHAR(length=32), nullable=False),
        sa.Column("manufacturer", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("transmission", sa.String(), nullable=False),
        sa.Column("engine_capacity", sa.String(), nullable=False),
        sa.Column("fuel_type", sa.String(), nullable=False),
        sa.Column("e_consumption_miles_per_kWh", sa.Float(), nullable=True),
        sa.Column("e_consumption_wh_per_km", sa.Float(), nullable=True),
        sa.Column("maximum_range_km", sa.Float(), nullable=True),
        sa.Column("maximum_range_miles", sa.Float(), nullable=True),
        sa.Column("metric_urban_cold", sa.Float(), nullable=True),
        sa.Column("metric_extra_urban", sa.Float(), nullable=True),
        sa.Column("metric_combined", sa.Float(), nullable=True),
        sa.Column("imperial_urban_cold", sa.Float(), nullable=True),
        sa.Column("imperial_extra_urban", sa.Float(), nullable=True),
        sa.Column("imperial_combined", sa.Float(), nullable=True),
        sa.Column("co2_g_per_km", sa.Float(), nullable=True),
        sa.Column("fuel_cost_6000_miles", sa.Float(), nullable=True),
        sa.Column("fuel_cost_12000_miles", sa.Float(), nullable=True),
        sa.Column("electricity_cost", sa.Float(), nullable=True),
        sa.Column("total_cost_per_12000_miles", sa.Float(), nullable=True),
        sa.Column("euro_standard", sa.String(), nullable=True),
        sa.Column("noise_level_dB_a_", sa.Float(), nullable=True),
        sa.Column("emissions_co_mg_per_km", sa.Float(), nullable=True),
        sa.Column("thc_emissions_mg_per_km", sa.Float(), nullable=True),
        sa.Column("emissions_nox_mg_per_km", sa.Float(), nullable=True),
        sa.Column("thc_plus_nox_emissions_mg_per_km", sa.Float(), nullable=True),
        sa.Column("particulates_no_mg_per_km", sa.Float(), nullable=True),
        sa.Column("rde_nox_urban", sa.Float(), nullable=True),
        sa.Column("rde_nox_combined", sa.Float(), nullable=True),
        sa.Column("date_of_change", sa.Date(), nullable=False),
        sa.Column("wiki_hashes", sa.ARRAY(sa.CHAR(length=32)), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_carfueldatacar_manufacturer"),
        "carfueldatacar",
        ["manufacturer"],
        unique=False,
    )
    op.create_table(
        "wikicarcategory",
        sa.Column("category_short_eu", sa.String(), nullable=False),
        sa.Column("category_name_de", sa.String(), nullable=False),
        sa.Column("category_name_en", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("category_short_eu"),
    )
    op.create_index(
        op.f("ix_wikicarcategory_category_name_de"),
        "wikicarcategory",
        ["category_name_de"],
        unique=True,
    )
    op.create_index(
        op.f("ix_wikicarcategory_category_name_en"),
        "wikicarcategory",
        ["category_name_en"],
        unique=True,
    )
    op.create_index(
        op.f("ix_wikicarcategory_category_short_eu"),
        "wikicarcategory",
        ["category_short_eu"],
        unique=False,
    )
    op.create_table(
        "carfueldataaveragecategorystatistics",
        sa.Column("id", sa.CHAR(length=32), nullable=False),
        sa.Column("vehicle_type", sa.String(), nullable=False),
        sa.Column("fuel_type", sa.String(), nullable=False),
        sa.Column("phenomenon_name", sa.String(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("numb_cars", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("category_short_eu", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["category_short_eu"], ["wikicarcategory.category_short_eu"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_carfueldataaveragecategorystatistics_fuel_type"),
        "carfueldataaveragecategorystatistics",
        ["fuel_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_carfueldataaveragecategorystatistics_id"),
        "carfueldataaveragecategorystatistics",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_carfueldataaveragecategorystatistics_phenomenon_name"),
        "carfueldataaveragecategorystatistics",
        ["phenomenon_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_carfueldataaveragecategorystatistics_vehicle_type"),
        "carfueldataaveragecategorystatistics",
        ["vehicle_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_carfueldataaveragecategorystatistics_year"),
        "carfueldataaveragecategorystatistics",
        ["year"],
        unique=False,
    )
    op.create_table(
        "wikicar",
        sa.Column("hash_id", sa.CHAR(length=32), nullable=False),
        sa.Column("wiki_name", sa.String(), nullable=False),
        sa.Column("category_short_eu", sa.String(), nullable=True),
        sa.Column("brand_name", sa.String(), nullable=False),
        sa.Column("car_name", sa.String(), nullable=False),
        sa.Column("page_id", sa.Integer(), nullable=True),
        sa.Column("page_language", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["category_short_eu"], ["wikicarcategory.category_short_eu"],
        ),
        sa.PrimaryKeyConstraint("hash_id"),
    )
    op.create_index(
        op.f("ix_wikicar_brand_name"), "wikicar", ["brand_name"], unique=False
    )
    op.create_index(op.f("ix_wikicar_car_name"), "wikicar", ["car_name"], unique=False)
    op.create_index(
        op.f("ix_wikicar_category_short_eu"),
        "wikicar",
        ["category_short_eu"],
        unique=False,
    )
    op.create_index(op.f("ix_wikicar_hash_id"), "wikicar", ["hash_id"], unique=False)
    op.create_index(
        op.f("ix_wikicar_wiki_name"), "wikicar", ["wiki_name"], unique=False
    )
    op.create_table(
        "wikicarpagetext",
        sa.Column("hash_id", sa.CHAR(length=32), nullable=False),
        sa.Column("wiki_name", sa.String(), nullable=False),
        sa.Column("brand_name", sa.String(), nullable=False),
        sa.Column("car_name", sa.String(), nullable=False),
        sa.Column("page_language", sa.String(), nullable=False),
        sa.Column("page_text", sa.String(), nullable=True),
        sa.Column("category_short_eu", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["category_short_eu"], ["wikicarcategory.category_short_eu"],
        ),
        sa.PrimaryKeyConstraint("hash_id"),
    )
    op.create_index(
        op.f("ix_wikicarpagetext_brand_name"),
        "wikicarpagetext",
        ["brand_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_wikicarpagetext_car_name"),
        "wikicarpagetext",
        ["car_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_wikicarpagetext_category_short_eu"),
        "wikicarpagetext",
        ["category_short_eu"],
        unique=False,
    )
    op.create_index(
        op.f("ix_wikicarpagetext_hash_id"), "wikicarpagetext", ["hash_id"], unique=False
    )
    op.create_index(
        op.f("ix_wikicarpagetext_page_language"),
        "wikicarpagetext",
        ["page_language"],
        unique=False,
    )
    op.create_index(
        op.f("ix_wikicarpagetext_wiki_name"),
        "wikicarpagetext",
        ["wiki_name"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_wikicarpagetext_wiki_name"), table_name="wikicarpagetext")
    op.drop_index(
        op.f("ix_wikicarpagetext_page_language"), table_name="wikicarpagetext"
    )
    op.drop_index(op.f("ix_wikicarpagetext_hash_id"), table_name="wikicarpagetext")
    op.drop_index(
        op.f("ix_wikicarpagetext_category_short_eu"), table_name="wikicarpagetext"
    )
    op.drop_index(op.f("ix_wikicarpagetext_car_name"), table_name="wikicarpagetext")
    op.drop_index(op.f("ix_wikicarpagetext_brand_name"), table_name="wikicarpagetext")
    op.drop_table("wikicarpagetext")
    op.drop_index(op.f("ix_wikicar_wiki_name"), table_name="wikicar")
    op.drop_index(op.f("ix_wikicar_hash_id"), table_name="wikicar")
    op.drop_index(op.f("ix_wikicar_category_short_eu"), table_name="wikicar")
    op.drop_index(op.f("ix_wikicar_car_name"), table_name="wikicar")
    op.drop_index(op.f("ix_wikicar_brand_name"), table_name="wikicar")
    op.drop_table("wikicar")
    op.drop_index(
        op.f("ix_carfueldataaveragecategorystatistics_year"),
        table_name="carfueldataaveragecategorystatistics",
    )
    op.drop_index(
        op.f("ix_carfueldataaveragecategorystatistics_vehicle_type"),
        table_name="carfueldataaveragecategorystatistics",
    )
    op.drop_index(
        op.f("ix_carfueldataaveragecategorystatistics_phenomenon_name"),
        table_name="carfueldataaveragecategorystatistics",
    )
    op.drop_index(
        op.f("ix_carfueldataaveragecategorystatistics_id"),
        table_name="carfueldataaveragecategorystatistics",
    )
    op.drop_index(
        op.f("ix_carfueldataaveragecategorystatistics_fuel_type"),
        table_name="carfueldataaveragecategorystatistics",
    )
    op.drop_table("carfueldataaveragecategorystatistics")
    op.drop_index(
        op.f("ix_wikicarcategory_category_short_eu"), table_name="wikicarcategory"
    )
    op.drop_index(
        op.f("ix_wikicarcategory_category_name_en"), table_name="wikicarcategory"
    )
    op.drop_index(
        op.f("ix_wikicarcategory_category_name_de"), table_name="wikicarcategory"
    )
    op.drop_table("wikicarcategory")
    op.drop_index(op.f("ix_carfueldatacar_manufacturer"), table_name="carfueldatacar")
    op.drop_table("carfueldatacar")
    # ### end Alembic commands ###

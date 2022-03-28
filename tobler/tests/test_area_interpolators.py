"""test interpolation functions."""
import geopandas

from libpysal.examples import load_example
from numpy.testing import assert_almost_equal
from tobler.area_weighted import area_interpolate
from tobler.area_weighted.area_interpolate import _area_tables_binning
from geopandas.testing import assert_geodataframe_equal
import pytest


def datasets():
    sac1 = load_example("Sacramento1")
    sac2 = load_example("Sacramento2")
    sac1 = geopandas.read_file(sac1.get_path("sacramentot2.shp"))
    sac2 = geopandas.read_file(sac2.get_path("SacramentoMSA2.shp"))
    sac1["pct_poverty"] = sac1.POV_POP / sac1.POV_TOT
    categories = ["cat", "dog", "donkey", "wombat", "capybara"]
    sac1["animal"] = (categories * ((len(sac1) // len(categories)) + 1))[: len(sac1)]

    return sac1, sac2


def test_area_interpolate_singlecore():
    sac1, sac2 = datasets()
    area = area_interpolate(
        source_df=sac1,
        target_df=sac2,
        extensive_variables=["TOT_POP"],
        intensive_variables=["pct_poverty"],
        categorical_variables=["animal"],
        n_jobs=1,
    )
    assert_almost_equal(area.TOT_POP.sum(), 1796856, decimal=0)
    assert_almost_equal(area.pct_poverty.sum(), 2140, decimal=0)
    assert_almost_equal(area.animal_cat.sum(), 32, decimal=0)
    assert_almost_equal(area.animal_dog.sum(), 19, decimal=0)
    assert_almost_equal(area.animal_donkey.sum(), 22, decimal=0)
    assert_almost_equal(area.animal_wombat.sum(), 23, decimal=0)
    assert_almost_equal(area.animal_capybara.sum(), 20, decimal=0)


def test_area_interpolate_custom_index():
    sac1, sac2 = datasets()
    sac1.index = sac1.index * 2
    sac2.index = sac2.index * 13
    area = area_interpolate(
        source_df=sac1,
        target_df=sac2,
        extensive_variables=["TOT_POP"],
        intensive_variables=["pct_poverty"],
        categorical_variables=["animal"],
    )
    assert_almost_equal(area.TOT_POP.sum(), 1796856, decimal=0)
    assert_almost_equal(area.pct_poverty.sum(), 2140, decimal=0)
    assert_almost_equal(area.animal_cat.sum(), 32, decimal=0)
    assert_almost_equal(area.animal_dog.sum(), 19, decimal=0)
    assert_almost_equal(area.animal_donkey.sum(), 22, decimal=0)
    assert_almost_equal(area.animal_wombat.sum(), 23, decimal=0)
    assert_almost_equal(area.animal_capybara.sum(), 20, decimal=0)
    assert not area.isna().any().any()


def test_area_interpolate_sindex_options():
    sac1, sac2 = datasets()
    auto = area_interpolate(
        source_df=sac1,
        target_df=sac2,
        extensive_variables=["TOT_POP"],
        intensive_variables=["pct_poverty"],
    )
    source = area_interpolate(
        source_df=sac1,
        target_df=sac2,
        extensive_variables=["TOT_POP"],
        intensive_variables=["pct_poverty"],
        spatial_index="source",
    )
    target = area_interpolate(
        source_df=sac1,
        target_df=sac2,
        extensive_variables=["TOT_POP"],
        intensive_variables=["pct_poverty"],
        spatial_index="target",
    )

    assert_geodataframe_equal(auto, source)
    assert_geodataframe_equal(auto, target)

    with pytest.raises(ValueError):
        area_interpolate(
            source_df=sac1,
            target_df=sac2,
            extensive_variables=["TOT_POP"],
            intensive_variables=["pct_poverty"],
            spatial_index="non-existent",
        )


def test_area_interpolate_parallel():
    sac1, sac2 = datasets()
    area = area_interpolate(
        source_df=sac1,
        target_df=sac2,
        extensive_variables=["TOT_POP"],
        intensive_variables=["pct_poverty"],
        n_jobs=-1,
    )
    assert_almost_equal(area.TOT_POP.sum(), 1796856, decimal=0)
    assert_almost_equal(area.pct_poverty.sum(), 2140, decimal=0)


def test_area_tables_binning():
    sac1, sac2 = datasets()

    auto = _area_tables_binning(source_df=sac1, target_df=sac2, spatial_index="auto")
    source = _area_tables_binning(
        source_df=sac1, target_df=sac2, spatial_index="source"
    )
    target = _area_tables_binning(
        source_df=sac1, target_df=sac2, spatial_index="target"
    )

    assert (auto != source).sum() == 0
    assert (auto != target).sum() == 0

    assert auto.sum() == pytest.approx(1.3879647)
    assert auto.mean() == pytest.approx(2.7552649e-05)

    assert (auto[5][0].toarray() > 0).sum() == 7
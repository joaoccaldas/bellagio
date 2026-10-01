"""The footprints the viewer builds, for 30 October 2022. Imports the real filter."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'blender'))
from asof import built_footprints

ROOT = os.path.join(os.path.dirname(__file__), '..')


class City2022(unittest.TestCase):
    def test_city_py_uses_the_filter(self):
        _test_city_py_uses_the_filter()

    def test_date_line_is_in_the_page_template(self):
        test_date_line_is_in_the_page_template()

    def test_strip_on_30_oct_2022(self):
        test_strip_on_30_oct_2022()

    def test_detailed_bellagio_still_loads(self):
        test_detailed_bellagio_still_loads()


def _test_city_py_uses_the_filter():
    src = open(os.path.join(ROOT, 'blender', 'city.py')).read()
    assert 'built_footprints' in src


def test_date_line_is_in_the_page_template():
    html = open(os.path.join(ROOT, 'web', 'index.template.html')).read()
    assert '30/10/2022' in html
    assert 'Las Vegas' in html
    assert 'Golden Knights' in html and 'T-Mobile Arena' in html
    # the line is in the fixed top brand, not inside a closed panel
    assert html.index('30/10/2022') < html.index('id="placesPanel"')


def test_strip_on_30_oct_2022():
    rows = built_footprints()
    names = [(r.get('name') or '') for r in rows]
    low = [n.lower() for n in names]
    ys = [r['c'][1] for r in rows]
    assert any(n == 'The Mirage Hotel & Casino' and r['h'] >= 90 for n, r in zip(names, rows))
    assert any(n == 'Tropicana Las Vegas' and r['h'] >= 20 for n, r in zip(names, rows))
    assert not any(n == 'sphere' or n.startswith('sphere ') or 'msg sphere' in n for n in low)
    assert not any('grand prix' in n or 'formula 1' in n or 'formula one' in n for n in low)
    assert not any('horseshoe' in n or 'hard rock' in n or 'vanderpump' in n for n in low)
    assert not any(n == 'new las vegas stadium' for n in low)
    assert any(n == 'the cromwell' for n in low)
    assert any(n == 'New York New York Hotel and Casino' and r['h'] >= 160 for n, r in zip(names, rows))
    assert any("bally's las vegas" in n for n in low)
    assert any('mandalay bay' in n for n in low)
    assert any(n.startswith('the strat') or 'sahara las vegas' in n for n in low)
    mandalay_y = min(r['c'][1] for r in rows if 'mandalay bay resort' in (r.get('name') or '').lower())
    assert min(ys) < mandalay_y - 80          # ground and buildings continue south of the resort
    north = max(r['c'][1] for r in rows if (r.get('name') or '').lower().startswith('the strat') or 'sahara las vegas hotel' in (r.get('name') or '').lower())
    assert north > 3000                        # north Strip, past the Bellagio
    # no gap big enough to split the Strip between Mandalay and the Strat
    band = sorted(y for y in ys if mandalay_y - 200 < y < north + 50)
    gaps = [b - a for a, b in zip(band, band[1:])]
    assert max(gaps) < 800


def test_detailed_bellagio_still_loads():
    src = open(os.path.join(ROOT, 'web', 'src', 'main.js')).read()
    assert "bellagio.glb" in src
    assert "ud.baked" in src
    assert "interior" in src and "penthouse" in src and "tower" in src


if __name__ == '__main__':
    unittest.main()

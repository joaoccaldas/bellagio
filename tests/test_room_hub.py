import json, pathlib, re, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORLD = json.loads((ROOT / "worlds/vegas/world.json").read_text())
LAB = (ROOT / "worlds/vegas/lab/index.html").read_text()
PLACES = (ROOT / "web/src/places.js").read_text()

class RoomHubTest(unittest.TestCase):
    def test_native_bellagio_inventory_is_complete(self):
        bellagio = next(z for z in WORLD["zones"] if z["id"] == "bellagio")
        ids = {r["semantic_id"] for r in bellagio["rooms"] if "semantic_id" in r}
        self.assertEqual(len(bellagio["rooms"]), 16)\n        aliases = {r.get("place_id"): r.get("parent_semantic_id") for r in bellagio["rooms"] if r.get("place_id")}\n        self.assertEqual(aliases.get("place:bellagio:fiori-di-como"), "room:bellagio:lobby")\n        self.assertEqual(aliases.get("place:bellagio:belvedere"), "zone:bellagio:roof-terrace")
        for required in {
            "room:bellagio:lobby","room:bellagio:conservatory",
            "room:bellagio:master-bath","room:bellagio:dressing",
            "room:bellagio:rotunda","zone:bellagio:roof-terrace"
        }:
            self.assertIn(required, ids)

    def test_final_kona_rooms_are_semantic_and_exact(self):
        lab = next(z for z in WORLD["zones"] if z["id"] == "caldas-3d-lab")
        rooms = {r["semantic_id"]: r for r in lab["rooms"]}
        self.assertEqual(set(rooms), {
            "room:konam:nor3-winter",
            "room:konam:beast-cave",
            "room:konam:breitling-kona"
        })
        for r in rooms.values():
            self.assertEqual(r["source_ref"], "cc80c48ada08a634c642561a64ef928f06c626be")
            self.assertEqual(r["recovery_pr"], 124)
            self.assertEqual(r["mode"], "canonical-embed")
            self.assertIn("reviewRoom=", r["runtime_entry"])

    def test_hub_uses_native_bellagio_flyto_and_final_kona_routes(self):
        self.assertIn("__goPlace", LAB)
        self.assertIn("data-place=\"Master bath\"", LAB)
        self.assertIn("data-place=\"Dressing room\"", LAB)
        for route in ["reviewRoom=nor3-winter","reviewRoom=beast-cave","reviewRoom=breitling-kona"]:
            self.assertIn(route, LAB)
        self.assertNotIn("norwegian-engine-review.html", LAB)
        self.assertNotIn("?room=breitling", LAB)

    def test_geometry_backed_missing_places_are_now_exposed(self):
        self.assertIn("name: 'Master bath'", PLACES)
        self.assertIn("name: 'Dressing room'", PLACES)
        self.assertIn("Ww.L1", PLACES)

if __name__ == "__main__":
    unittest.main()

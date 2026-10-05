import json, pathlib, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORLD = json.loads((ROOT / "worlds/vegas/world.json").read_text())
TEMPLATE = (ROOT / "web/index.template.html").read_text()
MAIN = (ROOT / "web/src/main.js").read_text()
PLACES = (ROOT / "web/src/places.js").read_text()
PAGES = (ROOT / ".github/workflows/pages.yml").read_text()
PORTAL = (ROOT / "portal/index.html").read_text()
LEGACY_LAB = (ROOT / "worlds/vegas/lab/index.html").read_text()

RECOVERY_REF = "363848cb1c311ad88d48eebbde160c518a34dc30"

class RoomHubTest(unittest.TestCase):
    def test_existing_bellagio_inventory_is_complete_and_not_duplicated(self):
        bellagio = next(z for z in WORLD["zones"] if z["id"] == "bellagio")
        self.assertEqual(len(bellagio["rooms"]), 16)
        ids = {r["semantic_id"] for r in bellagio["rooms"] if "semantic_id" in r}
        for required in {
            "room:bellagio:lobby",
            "room:bellagio:conservatory",
            "room:bellagio:master-bath",
            "room:bellagio:dressing",
            "room:bellagio:rotunda",
            "zone:bellagio:roof-terrace",
        }:
            self.assertIn(required, ids)
        self.assertEqual(PLACES.count("name: 'Master bath'"), 1)
        self.assertEqual(PLACES.count("name: 'Dressing room'"), 1)

    def test_room_index_lives_inside_the_existing_vegas_world(self):
        room_index = next(z for z in WORLD["zones"] if z["id"] == "room-index")
        self.assertEqual(room_index["entrypoint"], "/worlds/vegas/?rooms=1")
        self.assertEqual(room_index["host"], "bellagio-vegas")
        self.assertEqual(room_index["integration_mode"], "same-deployment-verified-embed")
        self.assertIn('id="roomsBtn"', TEMPLATE)
        self.assertIn('id="roomsPanel"', TEMPLATE)
        self.assertIn('id="roomOverlay"', TEMPLATE)
        self.assertNotIn('id="labBtn"', TEMPLATE)
        self.assertNotIn("location.href='lab/'", TEMPLATE)

    def test_final_kona_rooms_are_pinned_and_fail_closed_on_identity(self):
        room_index = next(z for z in WORLD["zones"] if z["id"] == "room-index")
        rooms = {r["semantic_id"]: r for r in room_index["rooms"]}
        self.assertEqual(set(rooms), {
            "room:konam:nor3-winter",
            "room:konam:beast-cave",
            "room:konam:breitling-kona",
        })
        for room in rooms.values():
            self.assertEqual(room["source_ref"], "cc80c48ada08a634c642561a64ef928f06c626be")
            self.assertEqual(room["recovery_ref"], RECOVERY_REF)
            self.assertTrue(room["runtime_entry"].startswith("kona-rooms/index.html?reviewRoom="))
            self.assertEqual(room["mode"], "same-origin-verified-embed")
        for semantic in rooms:
            self.assertIn(semantic, MAIN)
        self.assertIn("__reviewRoomIdentity", MAIN)
        self.assertIn("Blocked: wrong room identity", MAIN)
        self.assertIn("Blocked: exact room identity was not verified", MAIN)

    def test_pages_build_vendors_exact_recovery_into_vegas(self):
        self.assertIn("repository: joaoccaldas/konam", PAGES)
        self.assertIn(f"ref: {RECOVERY_REF}", PAGES)
        self.assertIn("path: _vendor/konam-final", PAGES)
        self.assertIn("_vendor/konam-final/_site/. _site/worlds/vegas/kona-rooms/", PAGES)
        self.assertIn("_site/worlds/vegas/kona-rooms/index.html", PAGES)
        self.assertNotIn("https://joaoccaldas.github.io/konam/?reviewRoom=", MAIN)

    def test_portal_and_legacy_lab_route_to_same_room_index(self):
        self.assertIn('href="worlds/vegas/?rooms=1"', PORTAL)
        self.assertNotIn("Bellagio Lab Wing", PORTAL)
        self.assertIn("../?rooms=1", LEGACY_LAB)

if __name__ == "__main__":
    unittest.main()

"""Tests for indexer module."""


from telegram_search.indexer import importer


class TestImporter:
    """Tests for importer module."""

    def test_import_json(self, tmp_path):
        """Test JSON import."""
        json_file = tmp_path / "test.json"
        json_file.write_text('[{"id": 1, "text": "test"}]')

        result = list(importer.import_json(json_file))
        assert len(result) == 1
        assert result[0]["text"] == "test"

    def test_import_csv(self, tmp_path):
        """Test CSV import."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,text\n1,hello\n2,world")

        result = list(importer.import_csv(csv_file))
        assert len(result) == 2

    def test_import_file_json(self, tmp_path):
        """Test import_file with JSON."""
        json_file = tmp_path / "data.json"
        json_file.write_text('[{"id": 1}]')

        result = list(importer.import_file(json_file))
        assert len(result) == 1

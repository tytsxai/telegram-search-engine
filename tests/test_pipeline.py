"""Tests for content processing pipeline."""


from telegram_search.pipeline import normalizer, tokenizer, deduper


class TestNormalizer:
    """Tests for normalizer module."""

    def test_normalize_unicode(self):
        """Test Unicode normalization."""
        text = "café"
        result = normalizer.normalize_unicode(text)
        assert result == "café"

    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        text = "hello   world\n\ttest"
        result = normalizer.normalize_whitespace(text)
        assert result == "hello world test"

    def test_to_simplified(self):
        """Test Traditional to Simplified conversion."""
        text = "電腦"
        result = normalizer.to_simplified(text)
        assert result == "电脑"

    def test_to_traditional(self):
        """Test Simplified to Traditional conversion."""
        text = "电脑"
        result = normalizer.to_traditional(text)
        assert result == "電腦"

    def test_to_pinyin(self):
        """Test Chinese to pinyin conversion."""
        text = "你好"
        result = normalizer.to_pinyin(text)
        assert result == "ni hao"

    def test_normalize_empty(self):
        """Test normalize with empty string."""
        assert normalizer.normalize("") == ""


class TestTokenizer:
    """Tests for tokenizer module."""

    def test_segment_chinese(self):
        """Test Chinese text segmentation."""
        text = "我爱北京天安门"
        tokens = tokenizer.segment(text)
        assert len(tokens) > 1
        assert "北京" in tokens

    def test_segment_empty(self):
        """Test empty string segmentation."""
        assert tokenizer.segment("") == []

    def test_segment_search(self):
        """Test search-optimized segmentation."""
        text = "中华人民共和国"
        tokens = tokenizer.segment_search(text)
        assert len(tokens) > 0


class TestDeduper:
    """Tests for deduper module."""

    def test_compute_simhash(self):
        """Test simhash computation."""
        text = "这是一段测试文本"
        result = deduper.compute_simhash(text)
        assert result.startswith("0x")

    def test_compute_simhash_empty(self):
        """Test simhash with empty string."""
        assert deduper.compute_simhash("") == "0"

    def test_hamming_distance(self):
        """Test Hamming distance calculation."""
        h1 = deduper.compute_simhash("测试文本一")
        h2 = deduper.compute_simhash("测试文本二")
        dist = deduper.hamming_distance(h1, h2)
        assert isinstance(dist, int)
        assert dist >= 0

    def test_is_duplicate_similar(self):
        """Test duplicate detection for similar texts."""
        h1 = deduper.compute_simhash("这是一段测试文本")
        h2 = deduper.compute_simhash("这是一段测试文本")
        assert deduper.is_duplicate(h1, h2) is True

    def test_is_duplicate_different(self):
        """Test duplicate detection for different texts."""
        h1 = deduper.compute_simhash("完全不同的内容")
        h2 = deduper.compute_simhash("Another text")
        assert deduper.is_duplicate(h1, h2, threshold=3) is False

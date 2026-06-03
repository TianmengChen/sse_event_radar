def test_import_package():
    import sse_event_radar

    assert sse_event_radar.__version__ == "0.1.0"


def test_import_collectors():
    from sse_event_radar.collectors.announcements import AnnouncementCollector
    from sse_event_radar.collectors.quotes import SSEQuoteCollector
    from sse_event_radar.collectors.stock_master import StockMasterCollector

    assert AnnouncementCollector
    assert SSEQuoteCollector
    assert StockMasterCollector

import unittest
from datetime import datetime, timedelta
from PySide6.QtWidgets import QApplication
import sys
import os

# Add parent directory (aerosar_dashboard) to sys.path so 'app' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.context import RetrievedContext
from app.models.incident import Location
from app.models.report import Report, IncidentSummary
from app.data.mock_provider import MockDataProvider
from app.services.data_service import DataService
from app.ui.widgets.report_list import ReportList, ReportRowWidget
from app.ui.widgets.report_detail import ReportDetail, RetrievedContextCard
from app.ui.views.reports_view import ReportsView
from app.ui.main_window import MainWindow

app = QApplication.instance() or QApplication(sys.argv)

class TestStep8Reports(unittest.TestCase):
    def test_report_models(self):
        ctx = RetrievedContext(
            source_id="SRC-001",
            source_type="Previous Observation",
            content="Person-like silhouette detected near search sector B.",
            relevance_score=0.94
        )
        self.assertEqual(ctx.source_id, "SRC-001")
        self.assertEqual(ctx.source_type, "Previous Observation")
        self.assertAlmostEqual(ctx.relevance_score, 0.94)

        summary = IncidentSummary(
            incident_id="INC-001",
            type="PERSON DETECTED",
            confidence=0.942,
            timestamp=datetime.now(),
            location=Location(x=12.4, y=8.7, z=14.8),
            status="CONFIRMED"
        )
        self.assertEqual(summary.incident_id, "INC-001")
        self.assertEqual(summary.location.x, 12.4)

        report = Report(
            report_id="RPT-001",
            incident_id="INC-001",
            mission_id="SAR-001",
            status="GENERATED",
            generated_at=datetime.now(),
            incident_summary=summary,
            ai_report="A person was detected within the surveyed search sector.",
            context_sources=[ctx],
            evidence_image="EV-INC-001.jpg",
            human_review_status="PENDING REVIEW"
        )
        self.assertEqual(report.report_id, "RPT-001")
        self.assertEqual(report.status, "GENERATED")
        self.assertEqual(report.human_review_status, "PENDING REVIEW")
        self.assertEqual(len(report.context_sources), 1)

    def test_data_provider_and_service(self):
        provider = MockDataProvider()
        service = DataService(provider)

        reports = service.get_reports()
        self.assertGreaterEqual(len(reports), 4)

        # Verify RPT-001 exists
        r1 = service.get_report("RPT-001")
        self.assertIsNotNone(r1)
        self.assertEqual(r1.incident_id, "INC-001")
        self.assertGreaterEqual(len(r1.context_sources), 1)

        # Verify lookup by incident ID
        r_by_inc = service.get_report_by_incident_id("INC-002")
        self.assertIsNotNone(r_by_inc)
        self.assertEqual(r_by_inc.report_id, "RPT-002")

        # Test human review via service
        r2 = service.get_report("RPT-002")
        self.assertIsNotNone(r2)
        self.assertEqual(r2.human_review_status, "PENDING REVIEW")
        success = service.review_report("RPT-002")
        self.assertTrue(success)
        self.assertEqual(r2.human_review_status, "REVIEWED")
        self.assertEqual(r2.status, "REVIEWED")

        # Verify audit event was logged
        events = service.get_events()
        review_events = [e for e in events if "RPT-002" in e.message and "REVIEWED" in e.message]
        self.assertGreaterEqual(len(review_events), 1)

    def test_report_list_widget(self):
        provider = MockDataProvider()
        reports = provider.get_reports()

        widget = ReportList()
        widget.set_reports(reports)

        self.assertIn(str(len(reports)), widget.count_badge.text())
        self.assertEqual(len(widget._row_widgets), len(reports))

        # Test selection signal
        received = []
        widget.report_selected.connect(lambda r: received.append(r))
        widget.select_report(reports[0])
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].report_id, reports[0].report_id)

        # Test filter tabs
        widget.set_filter("REVIEWED")
        for row in widget._row_widgets:
            self.assertTrue(row.report.status == "REVIEWED" or row.report.human_review_status == "REVIEWED")

        widget.set_filter("ALL")
        self.assertEqual(len(widget._row_widgets), len(reports))

    def test_report_detail_widget(self):
        provider = MockDataProvider()
        r1 = provider.get_report("RPT-001")
        assert r1 is not None

        detail = ReportDetail()
        detail.show_report(r1)

        self.assertIn("RPT-001", detail.val_report_id.text())
        self.assertIn("INC-001", detail.val_sub_tags.text())
        self.assertIn("PERSON", detail.val_inc_type.text())
        self.assertIn("12.4", detail.val_inc_x.text())
        self.assertIn("A person was detected", detail.val_ai_text.text())
        self.assertGreaterEqual(detail.context_items_layout.count(), 1)
        self.assertEqual(detail.val_meta_rpt.text(), "RPT-001")
        self.assertEqual(detail.val_meta_model.text(), "MOCK-RAG-LLM (SIMULATED)")

        # Test review button signal
        review_signals = []
        detail.review_report_requested.connect(lambda r_id: review_signals.append(r_id))
        detail.btn_mark_reviewed.click()
        # Since r1 was already reviewed, check signal emission with another report
        r3 = provider.get_report("RPT-003")
        assert r3 is not None
        detail.show_report(r3)
        self.assertEqual(detail.btn_mark_reviewed.text(), "MARK AS REVIEWED")
        detail.btn_mark_reviewed.click()
        self.assertEqual(len(review_signals), 1)
        self.assertEqual(review_signals[0], "RPT-003")

    def test_reports_view(self):
        view = ReportsView()
        self.assertIsNotNone(view.counters_bar)
        self.assertIsNotNone(view.report_list)
        self.assertIsNotNone(view.report_detail)

        # Pre-selected report
        self.assertIsNotNone(view.report_list.selected_report)

        # Test reviewing report updates view
        reports = view.data_service.get_reports()
        gen_reports = [r for r in reports if r.human_review_status == "PENDING REVIEW"]
        if gen_reports:
            target_id = gen_reports[0].report_id
            view._on_review_report(target_id)
            updated = view.data_service.get_report(target_id)
            assert updated is not None
            self.assertEqual(updated.human_review_status, "REVIEWED")

    def test_navigation_and_regression(self):
        win = MainWindow()
        win.show()

        # 1. Test navigating to Reports page (index 5)
        win.sidebar.set_active_page(5)
        win._on_page_changed(5, "Reports")
        self.assertEqual(win.stacked_widget.currentIndex(), 5)
        self.assertIn("REPORTS", win.header.page_title.text())

        # 2. Test cross-page jump from Reports to Incidents
        win.reports_view.navigate_to_incidents.emit("INC-001")
        self.assertEqual(win.stacked_widget.currentIndex(), 2)
        self.assertIn("INCIDENTS", win.header.page_title.text())

        # 3. Test cross-page jump from Incidents to Reports
        win.incidents_view.navigate_to_reports.emit("INC-001")
        self.assertEqual(win.stacked_widget.currentIndex(), 5)
        self.assertIn("REPORTS", win.header.page_title.text())

        # 4. Verify all 8 pages still navigate cleanly
        pages = ["Overview", "Live Feed", "Incidents", "Map", "Telemetry", "Reports", "Event Log", "Settings"]
        for idx, name in enumerate(pages):
            win.sidebar.set_active_page(idx)
            win._on_page_changed(idx, name)
            self.assertEqual(win.stacked_widget.currentIndex(), idx)

if __name__ == "__main__":
    unittest.main()

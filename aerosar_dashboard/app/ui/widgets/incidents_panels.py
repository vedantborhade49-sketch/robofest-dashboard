"""
Backward compatibility layer for Step 5 widgets.
Exports widgets from incident_list.py and incident_detail.py.
"""
from app.ui.widgets.incident_list import IncidentList, IncidentRowWidget
from app.ui.widgets.incident_detail import IncidentDetail, EvidenceFrameWidget
from app.ui.views.incidents_view import IncidentCountersBar, IncidentFilterBar

# Aliases for older naming conventions
IncidentListPanel = IncidentList
IncidentDetailPanel = IncidentDetail
IncidentCountersPanel = IncidentCountersBar
IncidentFilterPanel = IncidentFilterBar

__all__ = [
    "IncidentList",
    "IncidentDetail",
    "IncidentRowWidget",
    "EvidenceFrameWidget",
    "IncidentCountersBar",
    "IncidentFilterBar",
    "IncidentListPanel",
    "IncidentDetailPanel",
    "IncidentCountersPanel",
    "IncidentFilterPanel",
]

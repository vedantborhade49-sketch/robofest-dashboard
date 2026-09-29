from app.models.incident import Incident

class QueryBuilder:
    """Transforms a structured AEROSAR incident into a semantic retrieval query."""
    
    def build_query(self, incident: Incident) -> str:
        """
        Creates a query string focusing on the operational aspects of the incident.
        """
        inc_type = getattr(incident, "type", "UNKNOWN").replace("_", " ").lower()
        status = getattr(incident, "status", "NEW").lower()
        
        # Build query keywords based on incident properties
        query_parts = [
            inc_type,
            "response",
            "procedure",
            "protocol"
        ]
        
        # Add context if confidence is low
        if incident.confidence < 0.6:
            query_parts.append("low confidence")
            query_parts.append("verification")
            
        return " ".join(query_parts)

from app.models.incident import Incident

class QueryBuilder:
    """Transforms a structured AEROSAR incident into a semantic retrieval query."""
    
    def build_query(self, incident: Incident) -> str:
        """
        Creates a query string focusing on the operational aspects of the incident,
        including spatial context without raw sensor data.
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
            
        # Add spatial context
        if incident.spatial_status == "ESTIMATED" or incident.spatial_status == "CONFIRMED":
            query_parts.append("spatially located")
            if incident.range is not None:
                query_parts.append(f"range {incident.range:.1f}m")
            if incident.location:
                query_parts.append(f"location x {incident.location.x:.1f} y {incident.location.y:.1f}")
                
        return " ".join(query_parts)

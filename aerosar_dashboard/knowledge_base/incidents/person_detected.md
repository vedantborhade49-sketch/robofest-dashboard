# Person Detected Incident Guidelines

A "PERSON_DETECTED" incident indicates that the AI perception module (YOLO/OpenCV) has identified a human figure.
If the confidence score is above 80%, the incident is generally considered verified.
If the confidence score is low (below 60%), additional verification is required. This may involve repositioning the drone for a better angle or switching to an alternate sensor payload like thermal imaging.
The response to a person detected involves immediately logging the coordinates, capturing high-resolution evidence images, and notifying the mission commander.

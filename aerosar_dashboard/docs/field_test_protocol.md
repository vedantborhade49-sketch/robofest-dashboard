# AEROSAR Field Test Protocol

## 1. Introduction
This protocol dictates the process for moving tests out of the lab and into the physical environment. Flight testing is strictly prohibited until all static and ground validations pass.

## 2. Testing Phases

### Phase 1: Static Tests
*   **Setup**: UAV is powered on but disarmed.
*   **Actions**:
    1. Verify Pi boot sequence automatically initializes AEROSAR stack.
    2. Move a person in front of the stationary UAV.
    3. Confirm incident detection, localization, and transmission to the Ground Station.
*   **Sign-off required**: Yes.

### Phase 2: Controlled Ground Tests
*   **Setup**: UAV is walked around a test area by an operator.
*   **Actions**:
    1. Map a small physical space (e.g., parking lot or open field).
    2. Place obstacles and a designated target (person).
    3. Validate SLAM updates the mission map accurately based on movement.
    4. Validate telemetry (heading, position) reflects movement.
    5. Disconnect the Ground Station antenna mid-test. Verify local buffering on the Pi.
    6. Reconnect antenna. Verify synchronized incident transfer.
*   **Sign-off required**: Yes.

### Phase 3: Controlled Flight Tests
*   **Setup**: UAV performs a low-altitude manual hover.
*   **Actions**:
    1. Perform a short, controlled flight in an open area.
    2. Maintain line-of-sight to Ground Station.
    3. Confirm perception handles varying altitudes and angles.
    4. Confirm LLM Report generation operates correctly post-mission based on the flight data.
*   **Sign-off required**: Yes.

## 3. Search Scenario Execution
Once Phase 1-3 pass, set up a mock search scenario:
*   **Area**: Mixed terrain (open, structured, occluded).
*   **Target**: One partially visible person.
*   **Expected Outcome**: The dashboard must guide operators to the incident location, with spatial estimates distinguishing between known reference points and uncertainties.

## 4. Safety Constraints
*   Do NOT perform autonomous flight testing as part of this validation.
*   Do NOT modify YOLO confidence thresholds arbitrarily in the field without recorded data analysis.
*   All tests must record physical outcomes to `test_results.md`.

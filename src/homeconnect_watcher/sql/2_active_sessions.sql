CREATE OR REPLACE VIEW active_sessions AS

WITH with_session_start AS (
  SELECT
    event_id,
    appliance_id,
    event,
    timestamp,
    data,
    is_active,
    (is_active AND (LAG(is_active) OVER (PARTITION BY appliance_id ORDER BY timestamp, event_id) = False)) AS session_start
  FROM active_events
),

with_session_id AS (
  SELECT
    event_id,
    appliance_id,
    event,
    timestamp,
    data,
    is_active,
    SUM(session_start::int) OVER (PARTITION BY appliance_id ORDER BY timestamp, event_id) as session_id
  FROM with_session_start
)

SELECT * FROM with_session_id

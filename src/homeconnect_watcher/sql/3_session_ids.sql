CREATE OR REPLACE VIEW session_ids AS

WITH with_program AS (
  SELECT
    *,
    COALESCE(
        data->>'BSH.Common.Root.ActiveProgram',
        FIRST_VALUE(data->>'BSH.Common.Root.ActiveProgram') OVER (PARTITION BY appliance_id, session_id, grp ORDER BY timestamp, event)
    ) AS active_program
  FROM (
     SELECT
       *,
       COUNT(data->>'BSH.Common.Root.ActiveProgram') OVER (PARTITION BY appliance_id, session_id ORDER BY timestamp, event) as grp
     FROM active_sessions
  )
),

with_session_start AS (
  SELECT
    *,
    (
        (is_active AND (LAG(is_active) OVER (PARTITION BY appliance_id ORDER BY timestamp, event) = False))
        OR
        (active_program != (LAG(active_program) OVER (PARTITION BY appliance_id ORDER BY timestamp, event)))
        OR
        EXTRACT(EPOCH FROM (timestamp - LAG(timestamp) OVER (PARTITION BY appliance_id ORDER BY timestamp, event))) > 3600
    ) AS session_start
  FROM with_program
),

with_session_id AS (
  SELECT
    appliance_id,
    event,
    timestamp,
    data,
    is_active,
    SUM(session_start::int) OVER (PARTITION BY appliance_id ORDER BY timestamp, event) as session_id
  FROM with_session_start
)

SELECT * FROM with_session_id WHERE session_id > 0

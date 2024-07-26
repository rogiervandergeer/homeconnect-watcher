CREATE OR REPLACE VIEW v_raw_events_session_id AS

-- Session start labels to every first event that is active.
WITH with_session_start AS (
    SELECT
        appliance_id,
        event,
        timestamp,
        data,
        is_active,
        (is_active AND (lag(is_active) OVER (PARTITION BY appliance_id ORDER BY timestamp, event) = false)) AS session_start
    FROM v_raw_events_active
),

-- Add a session ID based on the session starts.
basic_session_id AS (
    SELECT
        appliance_id,
        event,
        timestamp,
        data,
        is_active,
        sum(session_start::int) OVER (PARTITION BY appliance_id ORDER BY timestamp, event) as session_id
    FROM with_session_start
),

-- Add the active program and forward fill by session.
session_id_with_program AS (
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
     FROM basic_session_id
  ) AS subquery
),

-- Recompute the session_start by including timeouts (1.5 hours of silence and program changes)
with_improved_session_start AS (
    SELECT
        *,
        (
            (
                is_active
                AND (lag(is_active) OVER (PARTITION BY appliance_id ORDER BY timestamp, event) = false)
                AND (lag(timestamp) OVER (PARTITION BY appliance_id ORDER BY timestamp, event) < timestamp)
            )
            OR
            (active_program != (lag(active_program) OVER (PARTITION BY appliance_id ORDER BY timestamp, event)))
            OR
            (
                is_active AND extract(EPOCH FROM
                    (timestamp - lag(timestamp) OVER (PARTITION BY appliance_id ORDER BY timestamp, event))
                ) > 5400
            )
        ) AS session_start
    FROM session_id_with_program
),

-- Recompute session ids based on improved session start
improved_session_id AS (
    SELECT
        appliance_id,
        event,
        timestamp,
        data,
        is_active,
        sum(session_start::int) OVER (PARTITION BY appliance_id ORDER BY timestamp, event) as session_id
    FROM with_improved_session_start
)

SELECT * FROM improved_session_id

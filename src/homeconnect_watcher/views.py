VIEWS = [
    """
CREATE OR REPLACE VIEW active_events AS

WITH actv AS (
    SELECT
        *,
        CASE
            WHEN event in ('CONNECTED', 'DISCONNECTED') THEN FALSE
            WHEN data->>'BSH.Common.Root.ActiveProgram' IS NOT NULL THEN TRUE
            WHEN data->>'BSH.Common.Status.OperationState' IS NULL THEN NULL
            WHEN data->>'BSH.Common.Status.OperationState' IN (
              'BSH.Common.EnumType.OperationState.Run',
              'BSH.Common.EnumType.OperationState.Pause',
              'BSH.Common.EnumType.OperationState.Aborting',
              'BSH.Common.EnumType.OperationState.DelayedStart'
            ) THEN TRUE
            ELSE FALSE
        END AS is_active
    FROM events
    WHERE appliance_id IS NOT NULL
)

SELECT 
    event_id,
    appliance_id,
    event,
    timestamp,
    data,
    COALESCE(is_active, FIRST_VALUE(is_active) OVER (PARTITION BY appliance_id, grp ORDER BY timestamp, event_id), FALSE) AS is_active
FROM (
    SELECT 
        *,
        COUNT(is_active) OVER (PARTITION BY appliance_id ORDER BY timestamp, event_id) as grp
    FROM actv
)
""",
    """
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

""",
    """
CREATE OR REPLACE VIEW session_ids AS

WITH with_program AS (
  SELECT 
    *,
    COALESCE(
        data->>'BSH.Common.Root.ActiveProgram',
        FIRST_VALUE(data->>'BSH.Common.Root.ActiveProgram') OVER (PARTITION BY appliance_id, session_id ORDER BY timestamp, event_id)
    ) AS active_program
  FROM (
     SELECT 
       *,
       COUNT(data->>'BSH.Common.Root.ActiveProgram') OVER (PARTITION BY appliance_id, session_id ORDER BY timestamp, event_id) as grp
     FROM active_sessions
  )
),

with_session_start AS (
  SELECT
    *,
    (
        (is_active AND (LAG(is_active) OVER (PARTITION BY appliance_id ORDER BY timestamp, event_id) = False))
        OR
        (active_program != (LAG(active_program) OVER (PARTITION BY appliance_id ORDER BY timestamp, event_id)))
        OR
        EXTRACT(EPOCH FROM (timestamp - LAG(timestamp) OVER (PARTITION BY appliance_id ORDER BY timestamp, event_id))) > 300
    ) AS session_start
  FROM with_program
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

SELECT * FROM with_session_id WHERE session_id > 0

""",
    """
CREATE OR REPLACE VIEW sessions AS

SELECT 
  appliance_id,
  session_id,
  MIN(timestamp) AS trigger_time,
  COALESCE(MIN(run_timestamp), MIN(timestamp)) AS start_time,
  MAX(timestamp) AS end_time,
  MIN(program) AS program,
  jsonb_object_agg(xkey, xvalue) AS agg_data
FROM (
  SELECT 
    appliance_id,
    session_id,
    timestamp,
    CASE
      WHEN 
        data->>'BSH.Common.Status.OperationState' = 'BSH.Common.EnumType.OperationState.Run'
        OR (
          data->>'BSH.Common.Option.RemainingProgramTime' IS NOT NULL
          AND data->>'BSH.Common.Option.FinishInRelative' IS NULL
        )
      THEN timestamp
    END AS run_timestamp,
    REVERSE(SPLIT_PART(REVERSE(data->>'BSH.Common.Root.ActiveProgram'), '.', 1)) AS program, 
    jsonb_each.key AS xkey, 
    jsonb_each.value AS xvalue
  FROM session_ids, jsonb_each(data)
  WHERE is_active
  ORDER BY timestamp ASC
) subquery
GROUP BY appliance_id, session_id
""",
]


def create_views(connection, drop: bool):
    if drop:
        with connection.cursor() as cursor:
            cursor.execute("DROP VIEW sessions")
    with connection.cursor() as cursor:
        for view in VIEWS:
            cursor.execute(view)
    connection.commit()
    connection.close()

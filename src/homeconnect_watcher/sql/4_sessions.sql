CREATE MATERIALIZED VIEW IF NOT EXISTS v_sessions AS

SELECT
  appliance_id,
  session_id,
  min(timestamp) AS trigger_time,
  coalesce(min(run_timestamp), min(timestamp)) AS start_time,
  max(timestamp) AS end_time,
  min(program) AS program,
  jsonb_object_agg(xkey, xvalue) AS session_details
FROM (
  SELECT
    appliance_id,
    session_id,
    timestamp,
    CASE
      WHEN
        data->>'BSH.Common.Status.OperationState' = 'BSH.Common.EnumType.OperationState.Run'
      THEN timestamp
    END AS run_timestamp,
    reverse(split_part(reverse(data->>'BSH.Common.Root.ActiveProgram'), '.', 1)) AS program,
    jsonb_each.key AS xkey,
    jsonb_each.value AS xvalue
  FROM v_raw_events_session_id, jsonb_each(data)
  WHERE is_active
  ORDER BY timestamp ASC
) AS subquery
GROUP BY appliance_id, session_id

CREATE MATERIALIZED VIEW sessions AS

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

CREATE OR REPLACE VIEW v_raw_events_active AS

-- Add an is_active label to each raw event.
-- An event is "active" (i.e. the appliance is running a program) when:
-- The OperationState represents an active state (running, finished, paused, aborting or delayed),
-- or there is an ActiveProgram (and the remaining program time > 0 or not defined).

WITH events_with_active_label AS (
    SELECT
        *,
        CASE
            -- Assume an appliance is inactive when just connected.
            WHEN event in ('CONNECTED', 'DISCONNECTED') THEN false
            WHEN data->>'BSH.Common.Event.ProgramFinished' = 'BSH.Common.EnumType.EventPresentState.Present' THEN false
            WHEN (
                data->>'BSH.Common.Root.ActiveProgram' IS NOT NULL
                AND (
                    data->>'BSH.Common.Option.RemainingProgramTime' <> '0'
                    OR NOT data ? 'BSH.Common.Option.RemainingProgramTime'
                )
            ) THEN true
            -- If the OperationState is unknown, then we do not know
            WHEN data->>'BSH.Common.Status.OperationState' IS NULL THEN NULL
            WHEN data->>'BSH.Common.Status.OperationState' IN (
              'BSH.Common.EnumType.OperationState.Run',
              'BSH.Common.EnumType.OperationState.Pause',
              'BSH.Common.EnumType.OperationState.Aborting',
              'BSH.Common.EnumType.OperationState.DelayedStart'
            ) THEN true
            ELSE false
        END AS is_active
    FROM events
    WHERE appliance_id IS NOT NULL
)

-- Forward fill is_active
SELECT
    appliance_id,
    event,
    timestamp,
    data,
    COALESCE(is_active, FIRST_VALUE(is_active) OVER (PARTITION BY appliance_id, grp ORDER BY timestamp, event), FALSE) AS is_active
FROM (
    SELECT
        *,
        COUNT(is_active) OVER (PARTITION BY appliance_id ORDER BY timestamp, event) as grp
    FROM events_with_active_label
) AS subquery

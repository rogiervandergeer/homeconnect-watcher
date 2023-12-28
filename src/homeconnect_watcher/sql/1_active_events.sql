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

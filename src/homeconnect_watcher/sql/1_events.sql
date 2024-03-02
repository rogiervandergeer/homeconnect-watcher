CREATE OR REPLACE VIEW v_events AS

-- Deduplicate EVENTs and find their respective end dates.

WITH expanded_events AS (
    SELECT
        "timestamp",
        appliance_id,
        jsonb_each_text.key AS event,
        jsonb_each_text.value = 'BSH.Common.EnumType.EventPresentState.Present'::text AS present
    FROM events,
        LATERAL jsonb_each_text(events.data) jsonb_each_text(key, value)
    WHERE event = 'EVENT'
        AND jsonb_each_text.key LIKE '%.Event.%'
),

unique_events AS (
    SELECT DISTINCT
        appliance_id,
        event
    FROM expanded_events
),

-- Create fake events with present=false of every known type at a disconnect.
disconnects AS (
    SELECT
        "timestamp",
        events.appliance_id,
        unique_events.event,
        false AS present
    FROM events
        LEFT JOIN unique_events ON events.appliance_id = unique_events.appliance_id
    WHERE events.event = 'DISCONNECTED'
),

expanded_events_with_start AS (
    SELECT
        "timestamp",
        appliance_id,
        event,
        present,
        present AND lag(present, 1, false) OVER (PARTITION BY appliance_id, event ORDER BY "timestamp") = false AS event_start
    FROM ((SELECT * FROM expanded_events) UNION ALL (SELECT * FROM disconnects)) AS total
),

expanded_events_with_id AS (
    SELECT
        "timestamp",
        appliance_id,
        event,
        present,
        sum(event_start::integer) OVER (PARTITION BY appliance_id, event ORDER BY "timestamp") AS event_id
    FROM expanded_events_with_start
)

SELECT
    appliance_id,
    reverse(split_part(reverse(event), '.', 1)) AS event,
    min("timestamp") AS start_time,
    min("timestamp") FILTER (WHERE present = false) AS end_time
FROM expanded_events_with_id
GROUP BY appliance_id, event, event_id
ORDER BY (min("timestamp"))

CREATE OR REPLACE VIEW combined_events AS


WITH with_event_start AS (
    SELECT
        "timestamp",
        appliance_id,
        event,
        present,
        present AND lag(present, 1, false) OVER (PARTITION BY appliance_id, event ORDER BY "timestamp") = false AS event_start
    FROM events_by_type
),

with_event_id AS (
    SELECT
        "timestamp",
        appliance_id,
        event,
        present,
        sum(event_start::integer) OVER (PARTITION BY appliance_id, event ORDER BY "timestamp") AS event_id
    FROM with_event_start
)

SELECT
    appliance_id,
    reverse(split_part(reverse(event), '.', 1)) AS event,
    min("timestamp") AS start_time,
    min("timestamp") FILTER (WHERE present = false) AS end_time
FROM with_event_id
GROUP BY appliance_id, event, event_id
ORDER BY (min("timestamp"))

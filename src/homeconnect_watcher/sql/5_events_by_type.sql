CREATE OR REPLACE VIEW events_by_type AS

SELECT
    "timestamp",
    appliance_id,
    jsonb_each_text.key AS event,
    jsonb_each_text.value = 'BSH.Common.EnumType.EventPresentState.Present'::text AS present
FROM events,
    LATERAL jsonb_each_text(events.data) jsonb_each_text(key, value)
WHERE event = 'EVENT' AND jsonb_each_text.key LIKE '%.Event.%'

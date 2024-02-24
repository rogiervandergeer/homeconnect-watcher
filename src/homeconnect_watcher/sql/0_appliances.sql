CREATE OR REPLACE VIEW v_appliances AS

-- Appliance types can be found from their programs:
-- A program consists of four or five parts, e.g.:
-- - ConsumerProducts.CoffeeMaker.Program.Beverage.EspressoMacchiato
-- - LaundryCare.Washer.Program.Wool
-- This is <Appliance Group>.<Appliance Type>.Program.[<Program Group>.]<Program Name>

SELECT DISTINCT
    appliance_id,
    SPLIT_PART(data->>'BSH.Common.Root.SelectedProgram', '.', 2) AS appliance_type
FROM events
WHERE event = 'NOTIFY'
    AND data->>'BSH.Common.Root.SelectedProgram' IS NOT NULL
ORDER BY appliance_id ASC

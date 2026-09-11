-- Temporary table matching the original PaySim CSV
CREATE TEMP TABLE paysim_import (
    step INTEGER,
    type VARCHAR(20),
    amount DECIMAL(15, 2),
    nameOrig VARCHAR(20),
    oldbalanceOrg DECIMAL(15, 2),
    newbalanceOrig DECIMAL(15, 2),
    nameDest VARCHAR(20),
    oldbalanceDest DECIMAL(15, 2),
    newbalanceDest DECIMAL(15, 2),
    isFraud INTEGER,
    isFlaggedFraud INTEGER
);


-- Copy the original CSV into the temporary table
COPY paysim_import (
    step,
    type,
    amount,
    nameOrig,
    oldbalanceOrg,
    newbalanceOrig,
    nameDest,
    oldbalanceDest,
    newbalanceDest,
    isFraud,
    isFlaggedFraud
)
FROM '/data/raw/paysim.csv'
WITH (
    FORMAT CSV,
    HEADER TRUE
);


-- Move the data into the permanent transactions table
INSERT INTO transactions (
    data_source,
    simulation_step,
    transaction_type,
    amount,
    origin_code,
    old_balance_origin,
    new_balance_origin,
    destination_code,
    old_balance_destination,
    new_balance_destination,
    actual_fraud,
    rule_flagged_fraud,
    transaction_status
)
SELECT
    'paysim',
    step,
    type,
    amount,
    nameOrig,
    oldbalanceOrg,
    newbalanceOrig,
    nameDest,
    oldbalanceDest,
    newbalanceDest,
    isFraud = 1,
    isFlaggedFraud = 1,
    'completed'
FROM paysim_import;

CREATE TABLE customers (
    customer_id BIGSERIAL PRIMARY KEY,

    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE accounts (
    account_id BIGSERIAL PRIMARY KEY,

    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id),

    -- PaySim does not contain account types.
    -- The user selects this when creating an account.
    account_type VARCHAR(20) NOT NULL
        CHECK (
            account_type IN (
                'checking',
                'savings'
            )
        ),

    balance DECIMAL(15, 2) NOT NULL
        DEFAULT 0.00
        CHECK (balance >= 0),

    -- Example: 0.0350 represents 3.5%.
    interest_rate DECIMAL(5, 4) NOT NULL
        DEFAULT 0.0000
        CHECK (interest_rate >= 0),

    account_status VARCHAR(20) NOT NULL
        DEFAULT 'active'
        CHECK (
            account_status IN (
                'active',
                'frozen',
                'closed'
            )
        ),

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE merchants (
    merchant_id BIGSERIAL PRIMARY KEY,

    merchant_code VARCHAR(20) UNIQUE NOT NULL,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE transactions (
    transaction_id BIGSERIAL PRIMARY KEY,

    -- Identifies where the transaction came from.
    data_source VARCHAR(20) NOT NULL
        CHECK (
            data_source IN (
                'paysim',
                'application'
            )
        ),

    -- PaySim provides this value.
    -- It is NULL for application transactions.
    simulation_step INTEGER
        CHECK (simulation_step >= 0),

    transaction_type VARCHAR(20) NOT NULL
        CHECK (
            transaction_type IN (
                'CASH_IN',
                'CASH_OUT',
                'DEBIT',
                'PAYMENT',
                'TRANSFER'
            )
        ),

    -- PaySim contains some zero-dollar records.
    -- Python will require application amounts to be greater than zero.
    amount DECIMAL(15, 2) NOT NULL
        CHECK (amount >= 0),

    -- PaySim: nameOrig
    -- Application: generated from the sender account.
    origin_code VARCHAR(20) NOT NULL,

    -- PaySim: oldbalanceOrg and newbalanceOrig
    old_balance_origin DECIMAL(15, 2) NOT NULL
        CHECK (old_balance_origin >= 0),

    new_balance_origin DECIMAL(15, 2) NOT NULL
        CHECK (new_balance_origin >= 0),

    -- PaySim: nameDest
    -- Application: generated from the receiver or merchant.
    destination_code VARCHAR(20) NOT NULL,

    -- PaySim: oldbalanceDest and newbalanceDest
    old_balance_destination DECIMAL(15, 2) NOT NULL
        CHECK (old_balance_destination >= 0),

    new_balance_destination DECIMAL(15, 2) NOT NULL
        CHECK (new_balance_destination >= 0),

    -- Known label from PaySim.
    -- NULL for new application transactions until confirmed.
    actual_fraud BOOLEAN,

    -- PaySim: isFlaggedFraud
    -- Application: result of an application fraud rule.
    rule_flagged_fraud BOOLEAN,

    -- These foreign keys are NULL for imported PaySim records.
    sender_account_id BIGINT
        REFERENCES accounts(account_id),

    receiver_account_id BIGINT
        REFERENCES accounts(account_id),

    merchant_id BIGINT
        REFERENCES merchants(merchant_id),

    transaction_status VARCHAR(20) NOT NULL
        DEFAULT 'pending'
        CHECK (
            transaction_status IN (
                'pending',
                'completed',
                'failed',
                'flagged'
            )
        ),

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    -- Every PaySim record must include its original step,
    -- fraud label, and rule-based flag.
    CHECK (
        data_source <> 'paysim'
        OR (
            simulation_step IS NOT NULL
            AND actual_fraud IS NOT NULL
            AND rule_flagged_fraud IS NOT NULL
        )
    )
);




CREATE TABLE fraud_predictions (
    prediction_id BIGSERIAL PRIMARY KEY,

    transaction_id BIGINT NOT NULL
        REFERENCES transactions(transaction_id),

    fraud_probability DECIMAL(6, 5) NOT NULL
        CHECK (
            fraud_probability >= 0
            AND fraud_probability <= 1
        ),

    predicted_fraud BOOLEAN NOT NULL,

    model_version VARCHAR(50) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (transaction_id, model_version)
);


-- Machine-learning training view
CREATE OR REPLACE VIEW ml_training_features AS
SELECT
    transaction_id,
    transaction_type,
    amount,
    old_balance_origin,
    new_balance_origin,
    old_balance_destination,
    new_balance_destination,
    actual_fraud AS is_fraud
FROM transactions
WHERE data_source = 'paysim'
  AND actual_fraud IS NOT NULL;
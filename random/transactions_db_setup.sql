CREATE TABLE payment_type (
    id          SMALLSERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    is_outgoing BOOLEAN NOT NULL
);

CREATE TABLE tag (
    id   SERIAL PRIMARY KEY,
    tag  TEXT NOT NULL UNIQUE
);

CREATE TABLE account (
    id               SERIAL PRIMARY KEY,
    account_number   TEXT NOT NULL,
    account_holder   TEXT,
    description      TEXT,
    UNIQUE (account_number)
);

CREATE TABLE transaction (
    id                      SERIAL PRIMARY KEY,
    date_posted             DATE NOT NULL,
    date_paid               DATE,
    payment_type_id         SMALLINT NOT NULL REFERENCES payment_type(id),
    counterparty_account_id INTEGER REFERENCES account(id),
    amount                  NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    fee                     NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (fee >= 0),
    currency                CHAR(3) NOT NULL DEFAULT 'CZK',
    note                    TEXT,
    bank_transaction_id     BIGINT NOT NULL UNIQUE
);

CREATE TABLE transaction_tag (
    transaction_id INTEGER NOT NULL REFERENCES transaction(id) ON DELETE CASCADE,
    tag_id         INTEGER NOT NULL REFERENCES tag(id) ON DELETE CASCADE,
    PRIMARY KEY (transaction_id, tag_id)
);

CREATE TABLE account_tag (
    account_id INTEGER NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    tag_id     INTEGER NOT NULL REFERENCES tag(id) ON DELETE CASCADE,
    PRIMARY KEY (account_id, tag_id)
);

CREATE INDEX idx_transaction_date_posted  ON transaction (date_posted);
CREATE INDEX idx_transaction_payment_type ON transaction (payment_type_id);
CREATE INDEX idx_transaction_counterparty ON transaction (counterparty_account_id);
CREATE INDEX idx_transaction_tag_tag_id   ON transaction_tag (tag_id);
CREATE INDEX idx_account_tag_tag_id       ON account_tag (tag_id);

DROP VIEW IF EXISTS transaction_enriched;
CREATE VIEW transaction_enriched AS
SELECT
    t.id,
    t.date_posted,
    t.date_paid,
    pt.name        AS payment_type,
    pt.is_outgoing AS is_outgoing,
    CASE
        WHEN pt.is_outgoing THEN -t.amount
        ELSE t.amount
    END AS signed_amount,
    t.amount       AS amount_abs,
    t.fee,
    t.currency,
    CASE
        WHEN pt.is_outgoing THEN -t.amount - t.fee
        ELSE t.amount - t.fee
    END AS net_amount,
    a.account_number   AS counterparty_account_number,
    a.account_holder   AS counterparty_account_holder,
    t.note,
    t.bank_transaction_id,
    COALESCE(array_agg(DISTINCT tg.tag)
             FILTER (WHERE tg.tag IS NOT NULL), '{}') AS tags,
    COALESCE(array_agg(DISTINCT atg.tag)
             FILTER (WHERE atg.tag IS NOT NULL), '{}') AS account_tags
FROM transaction t
JOIN payment_type pt
  ON t.payment_type_id = pt.id
LEFT JOIN account a
  ON t.counterparty_account_id = a.id
LEFT JOIN transaction_tag tt
  ON tt.transaction_id = t.id
LEFT JOIN tag tg
  ON tg.id = tt.tag_id
LEFT JOIN account_tag at
  ON at.account_id = a.id
LEFT JOIN tag atg
  ON atg.id = at.tag_id
GROUP BY
    t.id, t.date_posted, t.date_paid,
    pt.name, pt.is_outgoing,
    t.amount, t.fee, t.currency,
    a.account_number, a.account_holder,
    t.note, t.bank_transaction_id;

DROP VIEW IF EXISTS transaction_latest_dates;
CREATE VIEW transaction_latest_dates AS
SELECT
    MAX(date_posted) AS latest_date_posted,
    MAX(date_paid)   AS latest_date_paid,
    CURRENT_DATE - MAX(date_posted) AS days_since_posted,
    CURRENT_DATE - MAX(date_paid)   AS days_since_paid
FROM transaction;

-- =============================================
-- Crednexa AI — Full Database Schema
-- =============================================
-- Safe to run multiple times (IF NOT EXISTS).
-- Keep this file as the single source of truth.
-- =============================================

-- ─── 1. CLIENTS ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS clients (
    client_id         TEXT    PRIMARY KEY,
    company_name      TEXT    NOT NULL,
    contact_name      TEXT    DEFAULT '',
    contact_email     TEXT    DEFAULT '',
    phone             TEXT    DEFAULT '',
    industry          TEXT    DEFAULT '',
    total_outstanding REAL    DEFAULT 0,
    total_paid        REAL    DEFAULT 0,
    invoices_count    INTEGER DEFAULT 0,
    risk_category     TEXT    DEFAULT 'Low',     -- Low | Medium | High | Critical
    notes             TEXT    DEFAULT '',
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─── 2. INVOICES ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id     TEXT    PRIMARY KEY,
    client_id      TEXT    NOT NULL REFERENCES clients(client_id),
    invoice_number TEXT    UNIQUE NOT NULL,
    amount         REAL    NOT NULL,
    amount_paid    REAL    DEFAULT 0,
    currency       TEXT    DEFAULT 'INR',
    issue_date     DATE    NOT NULL,
    due_date       DATE    NOT NULL,
    overdue_days   INTEGER DEFAULT 0,
    status         TEXT    DEFAULT 'Pending',   -- Pending | Overdue | Partially Paid | Paid | Written Off
    severity       TEXT    DEFAULT 'None',      -- None | Low | Medium | High | Critical
    payment_terms  TEXT    DEFAULT '',
    notes          TEXT    DEFAULT '',
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─── 3. EMAIL LOGS ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS email_logs (
    email_id         TEXT PRIMARY KEY,
    invoice_id       TEXT REFERENCES invoices(invoice_id),
    client_id        TEXT NOT NULL REFERENCES clients(client_id),
    subject          TEXT NOT NULL,
    body             TEXT NOT NULL,
    tone             TEXT NOT NULL,
    tone_level       INTEGER DEFAULT 1,
    status           TEXT DEFAULT 'Draft',        -- Draft | Pending Approval | Approved | Rejected | Sent | Failed
    approved_by      TEXT    DEFAULT '',
    approved_at      DATETIME,
    sent_at          DATETIME,
    send_status      TEXT    DEFAULT '',
    ai_model_used    TEXT    DEFAULT '',
    detected_emotion TEXT    DEFAULT '',
    confidence_score REAL    DEFAULT 0,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─── 4. PAYMENT PROMISES ─────────────────────────────────
CREATE TABLE IF NOT EXISTS payment_promises (
    promise_id      TEXT PRIMARY KEY,
    client_id       TEXT NOT NULL REFERENCES clients(client_id),
    invoice_id      TEXT REFERENCES invoices(invoice_id),
    promised_amount REAL NOT NULL,
    promised_date   DATE NOT NULL,
    status          TEXT DEFAULT 'Pending',       -- Pending | Fulfilled | Broken | Renegotiated
    source          TEXT DEFAULT '',
    notes           TEXT DEFAULT '',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─── 5. RISK SCORES ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS risk_scores (
    score_id              TEXT PRIMARY KEY,
    client_id             TEXT NOT NULL REFERENCES clients(client_id),
    risk_score            REAL NOT NULL,           -- 0.0 – 100.0
    risk_category         TEXT NOT NULL,            -- Low | Medium | High | Critical
    contributing_factors  TEXT DEFAULT '{}',        -- JSON
    payment_reliability   REAL DEFAULT 1.0,
    avg_days_overdue      REAL DEFAULT 0,
    total_overdue_count   INTEGER DEFAULT 0,
    calculated_at         DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─── 6. RECOVERY STRATEGIES ─────────────────────────────
CREATE TABLE IF NOT EXISTS recovery_strategies (
    strategy_id         TEXT PRIMARY KEY,
    client_id           TEXT NOT NULL REFERENCES clients(client_id),
    strategy_type       TEXT NOT NULL,              -- Negotiation | Installment | Discount | Legal | Write-Off
    description         TEXT NOT NULL,
    recommended_actions TEXT DEFAULT '[]',           -- JSON array
    priority            TEXT DEFAULT 'Medium',
    status              TEXT DEFAULT 'Proposed',     -- Proposed | Active | Completed | Abandoned
    ai_reasoning        TEXT DEFAULT '',
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─── 7. TONE FEEDBACK (self-learning) ───────────────────
CREATE TABLE IF NOT EXISTS tone_feedback (
    feedback_id          TEXT PRIMARY KEY,
    email_id             TEXT NOT NULL REFERENCES email_logs(email_id),
    tone_used            TEXT NOT NULL,
    client_response      TEXT DEFAULT '',
    detected_outcome     TEXT DEFAULT 'No Response', -- Positive | Neutral | Negative | No Response
    effectiveness_score  REAL DEFAULT 0.5,
    notes                TEXT DEFAULT '',
    created_at           DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─── 8. AUDIT LOGS ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id        TEXT     PRIMARY KEY,
    user_action   TEXT     NOT NULL,    -- Upload | Generate | Approve | Reject | Send | Edit | Delete
    entity_type   TEXT     NOT NULL,    -- Invoice | Email | Client | Strategy | Promise
    entity_id     TEXT     DEFAULT '',
    details       TEXT     DEFAULT '',  -- JSON
    performed_by  TEXT     DEFAULT 'System',
    performed_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ═════════════════════════════════════════════════════════
-- INDEXES — for frequently-filtered columns
-- ═════════════════════════════════════════════════════════
CREATE INDEX IF NOT EXISTS idx_invoices_client     ON invoices(client_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status     ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_due_date   ON invoices(due_date);
CREATE INDEX IF NOT EXISTS idx_invoices_severity   ON invoices(severity);
CREATE INDEX IF NOT EXISTS idx_email_logs_client   ON email_logs(client_id);
CREATE INDEX IF NOT EXISTS idx_email_logs_status   ON email_logs(status);
CREATE INDEX IF NOT EXISTS idx_risk_scores_client  ON risk_scores(client_id);
CREATE INDEX IF NOT EXISTS idx_audit_entity        ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_promises_client     ON payment_promises(client_id);
CREATE INDEX IF NOT EXISTS idx_promises_status     ON payment_promises(status);

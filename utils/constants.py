"""
Constants, enums, and status codes used throughout the application.
"""

from enum import Enum


class InvoiceStatus(str, Enum):
    PENDING = "Pending"
    OVERDUE = "Overdue"
    PARTIALLY_PAID = "Partially Paid"
    PAID = "Paid"
    WRITTEN_OFF = "Written Off"


class Severity(str, Enum):
    NONE = "None"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ToneLevel(str, Enum):
    FRIENDLY = "Friendly"
    PROFESSIONAL = "Professional"
    FIRM = "Firm"
    URGENT = "Urgent"
    LEGAL = "Legal"


class EmailStatus(str, Enum):
    DRAFT = "Draft"
    PENDING_APPROVAL = "Pending Approval"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    SENT = "Sent"
    FAILED = "Failed"


class SendStatus(str, Enum):
    SUCCESS = "Success"
    FAILED = "Failed"
    BOUNCED = "Bounced"


class PromiseStatus(str, Enum):
    PENDING = "Pending"
    FULFILLED = "Fulfilled"
    BROKEN = "Broken"
    RENEGOTIATED = "Renegotiated"


class RiskCategory(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class StrategyType(str, Enum):
    NEGOTIATION = "Negotiation"
    INSTALLMENT = "Installment"
    DISCOUNT = "Discount"
    LEGAL = "Legal"
    WRITE_OFF = "Write-Off"


class StrategyStatus(str, Enum):
    PROPOSED = "Proposed"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    ABANDONED = "Abandoned"


class EmotionType(str, Enum):
    HAPPY = "Happy"
    NEUTRAL = "Neutral"
    FRUSTRATED = "Frustrated"
    ANGRY = "Angry"
    DESPERATE = "Desperate"
    COOPERATIVE = "Cooperative"


class AuditAction(str, Enum):
    UPLOAD = "Upload"
    GENERATE = "Generate"
    APPROVE = "Approve"
    REJECT = "Reject"
    SEND = "Send"
    EDIT = "Edit"
    DELETE = "Delete"
    LOGIN = "Login"


class EntityType(str, Enum):
    INVOICE = "Invoice"
    EMAIL = "Email"
    CLIENT = "Client"
    STRATEGY = "Strategy"
    PROMISE = "Promise"


class ToneOutcome(str, Enum):
    POSITIVE = "Positive"
    NEUTRAL = "Neutral"
    NEGATIVE = "Negative"
    NO_RESPONSE = "No Response"


# ── Required CSV/Excel columns ────────────────────────────────────────
REQUIRED_INVOICE_COLUMNS = [
    "invoice_number",
    "company_name",
    "contact_email",
    "amount",
    "issue_date",
    "due_date",
]

OPTIONAL_INVOICE_COLUMNS = [
    "contact_name",
    "phone",
    "industry",
    "amount_paid",
    "currency",
    "payment_terms",
    "notes",
]

# ── Severity color mapping ────────────────────────────────────────────
SEVERITY_COLORS = {
    "None": "#6B7280",
    "Low": "#22C55E",
    "Medium": "#F59E0B",
    "High": "#EF4444",
    "Critical": "#DC2626",
}

RISK_COLORS = {
    "Low": "#22C55E",
    "Medium": "#F59E0B",
    "High": "#EF4444",
    "Critical": "#7C3AED",
}

TONE_COLORS = {
    "Friendly": "#22C55E",
    "Professional": "#3B82F6",
    "Firm": "#F59E0B",
    "Urgent": "#EF4444",
    "Legal": "#7C3AED",
}

STATUS_COLORS = {
    "Pending": "#6B7280",
    "Overdue": "#EF4444",
    "Partially Paid": "#F59E0B",
    "Paid": "#22C55E",
    "Written Off": "#9CA3AF",
}

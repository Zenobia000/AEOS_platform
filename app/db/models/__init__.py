"""ORM models — 依 docs/2-contracts/db-schema.md.

每個 model 一個檔案；本 __init__ 集中 re-export 給 alembic env 用。
"""

from app.db.models.api_key import ApiKey
from app.db.models.audit_log import AuditLog
from app.db.models.conversation import Conversation
from app.db.models.conversation_handoff import ConversationHandoff
from app.db.models.employee import Employee
from app.db.models.ingestion_job import IngestionJob
from app.db.models.knowledge_card import KnowledgeCard
from app.db.models.message import Message
from app.db.models.tenant import Tenant

__all__ = [
    "ApiKey",
    "AuditLog",
    "Conversation",
    "ConversationHandoff",
    "Employee",
    "IngestionJob",
    "KnowledgeCard",
    "Message",
    "Tenant",
]

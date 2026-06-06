from app.handlers.core_handler import register_core_handlers
from app.handlers.goal_handler import register_goal_handlers
from app.handlers.context_handler import register_context_handlers
from app.handlers.reasoning_handler import register_reasoning_handlers
from app.handlers.intelligence_handler import register_intelligence_handlers
from app.handlers.system_handler import register_system_handlers
from app.handlers.governance_handler import register_governance_handlers
from app.handlers.security_handler import register_security_handlers
from app.handlers.ingestion_handler import register_ingestion_handlers




def register_handlers(dp):

    register_core_handlers(dp)
    register_goal_handlers(dp)
    register_context_handlers(dp)
    register_reasoning_handlers(dp)
    register_intelligence_handlers(dp)
    register_system_handlers(dp)

    register_governance_handlers(dp)   # ← MUST exist
    register_security_handlers(dp)

    register_ingestion_handlers(dp)
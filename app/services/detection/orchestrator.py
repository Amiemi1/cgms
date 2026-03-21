from typing import Optional, Dict

from app.services.detection.task_detector import detect_task
from app.services.detection.event_detector import detect_event
from app.services.detection.decision_detector import detect_decision


# =========================
# MAIN ORCHESTRATOR
# =========================

def orchestrate(text: str) -> Optional[Dict]:
    """
    Central detection pipeline.

    Returns:
    {
        "type": "task" | "event" | "decision",
        "summary": str
    }
    """

    if not text:
        return None

    text = text.strip()

    # 🔹 1. Decision detection (highest confidence)
    decision = detect_decision(text)
    if decision:
        return {
            "type": "decision",
            "summary": decision
        }

    # 🔹 2. Event detection
    event = detect_event(text)
    if event:
        return {
            "type": "event",
            "summary": event
        }

    # 🔹 3. Task detection
    task = detect_task(text)
    if task:
        return {
            "type": "task",
            "summary": task
        }

    # 🔹 4. Nothing detected
    return None


# =========================
# PUBLIC INTERFACE (USED BY BOT)
# =========================

def detect(text: str) -> Optional[Dict]:
    """
    Public wrapper used by main.py
    Ensures safe execution.
    """

    try:
        return orchestrate(text)

    except Exception as e:
        print("❌ DETECTION ERROR:", e)
        return None
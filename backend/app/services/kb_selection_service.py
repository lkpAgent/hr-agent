"""
KB selection service: list user documents and use LLM to select the best-matching document
for a given question, then return its knowledge_base_id.
"""
import logging
import json
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm_service import LLMService
from app.services.lightweight_document_service import LightweightDocumentService

logger = logging.getLogger(__name__)


class KBSelectionService:
    """Service to auto-select a knowledge base by ranking documents with LLM"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_service = LLMService()
        self.document_service = LightweightDocumentService(db)

    async def list_candidates(
        self,
        user_id: UUID,
        max_candidates: int = 100,
    ) -> List[Dict[str, Any]]:
        """List candidate documents (id, filename, knowledge_base_id) for a user.
        Limits to max_candidates to control token usage.
        """
        try:
            documents = await self.document_service.get_user_documents(
                user_id=user_id,
                skip=0,
                limit=max_candidates,
            )
            candidates: List[Dict[str, Any]] = []
            for doc in documents:
                candidates.append({
                    "document_id": str(doc.id),
                    "filename": doc.filename,
                    "knowledge_base_id": str(doc.knowledge_base_id) if doc.knowledge_base_id else None,
                })
            return candidates
        except Exception as e:
            logger.error(f"Error listing candidate documents: {e}")
            raise

    async def select_best_document(
        self,
        question: str,
        candidates: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """Use LLM to select the best matching document from candidates.
        Returns a dict with keys: document_id, confidence, reason (optional).
        """
        if not candidates:
            return None

        # Prepare compact candidate list to minimize tokens
        # Only pass filename and document_id (and include kb id for downstream mapping if needed)
        compact = [
            {
                "document_id": c.get("document_id"),
                "filename": c.get("filename"),
            }
            for c in candidates
        ]

        system_prompt = (
            "You are an expert selector. Given a user question and a list of documents "
            "(each with document_id and filename), choose the single most relevant document. "
            "Respond ONLY with valid JSON: {\"document_id\": string, \"confidence\": number, \"reason\": string}. "
            "Confidence is in [0,1]. No extra commentary."
        )
        user_message = (
            "Question: " + question + "\n\n" +
            "Documents: " + json.dumps(compact, ensure_ascii=False)
        )

        try:
            # Use deterministic selection
            response = await self.llm_service.client.chat.completions.create(
                model=self.llm_service.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0,
                max_tokens=400,
            )
            content = response.choices[0].message.content.strip()
            # Attempt to parse JSON
            selected: Dict[str, Any] = json.loads(content)
            # Basic validation
            if not isinstance(selected, dict) or "document_id" not in selected:
                logger.warning(f"Invalid LLM selection output: {content}")
                return None
            return selected
        except Exception as e:
            logger.error(f"Error selecting best document via LLM: {e}")
            return None

    async def select_kb_for_question(
        self,
        question: str,
        user_id: UUID,
        max_candidates: int = 100,
    ) -> Dict[str, Any]:
        """High-level method: list candidates, ask LLM to select best, return KB ID.
        Returns: { knowledge_base_id, document_id, filename, confidence, reason, candidates_count }
        """
        candidates = await self.list_candidates(user_id=user_id, max_candidates=max_candidates)
        selection = await self.select_best_document(question=question, candidates=candidates)

        if not selection:
            return {
                "knowledge_base_id": None,
                "document_id": None,
                "filename": None,
                "confidence": 0.0,
                "reason": "No selection or no candidates",
                "candidates_count": len(candidates),
            }

        selected_doc_id = selection.get("document_id")
        confidence = selection.get("confidence", 0.0)
        reason = selection.get("reason", "")

        # Find the selected candidate to get kb id and filename
        selected_candidate = next((c for c in candidates if c["document_id"] == selected_doc_id), None)
        if not selected_candidate:
            return {
                "knowledge_base_id": None,
                "document_id": selected_doc_id,
                "filename": None,
                "confidence": confidence,
                "reason": reason or "Selected document not in candidate list",
                "candidates_count": len(candidates),
            }

        return {
            "knowledge_base_id": selected_candidate.get("knowledge_base_id"),
            "document_id": selected_doc_id,
            "filename": selected_candidate.get("filename"),
            "confidence": confidence,
            "reason": reason,
            "candidates_count": len(candidates),
        }
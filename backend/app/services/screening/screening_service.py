import logging
import json
from rapidfuzz import process, fuzz
from typing import Callable, AsyncGenerator

from app.domain.interfaces import IUnitOfWork, ICacheProvider

logger = logging.getLogger("sentinelai.services.screening")

class ScreeningService:
    def __init__(
        self,
        uow_factory: Callable[[], AsyncGenerator[IUnitOfWork, None]],
        cache: ICacheProvider
    ):
        self.uow_factory = uow_factory
        self.cache = cache
        self.MATCH_THRESHOLD = 85.0

    async def _get_active_entities(self) -> list[tuple[str, str]]:
        # Check cache first
        cached = await self.cache.get("active_entities")
        if cached:
            return cached

        # Fetch from DB if not in cache
        uow_gen = self.uow_factory()
        uow = await anext(uow_gen)
        async with uow:
            entities = await uow.entities.get_all_names()
            sanctions = await uow.sanctions.get_active_names()
        
        try:
            await anext(uow_gen)
        except StopAsyncIteration:
            pass

        combined = entities + sanctions
        await self.cache.set("active_entities", combined, ttl_seconds=300) # 5 mins
        return combined

    async def screen_pending_events(self) -> list[dict]:
        """Fetches pending raw events, screens them, and prepares state for the LLM."""
        screened_payloads = []
        
        uow_gen = self.uow_factory()
        uow = await anext(uow_gen)
        
        async with uow:
            pending = await uow.raw_events.get_unprocessed(limit=10)
            if not pending:
                return []

            active_names = await self._get_active_entities()
            # rapidfuzz expects choices as a dictionary for easy mapping back to IDs
            choices = {id_str: name for id_str, name in active_names}

            for event in pending:
                payload = json.loads(event.content)
                
                # Naive heuristic: Extract names from the event text. 
                # In reality, this might use NER (spaCy). Here we just match the whole text
                # or a 'name' field if present against the sanctions list.
                text_to_screen = payload.get("name") or payload.get("title") or payload.get("description", "")

                matches = process.extract(
                    text_to_screen, 
                    choices, 
                    scorer=fuzz.token_set_ratio, 
                    limit=5, 
                    score_cutoff=self.MATCH_THRESHOLD
                )
                
                # matches format: (matched_name, score, id_str)
                screening_matches = []
                for matched_name, score, id_str in matches:
                    screening_matches.append({
                        "id": id_str,
                        "name": matched_name,
                        "score": score
                    })

                # Prepare the AuditorState dictionary that will be passed to the LangGraph
                auditor_state = {
                    "raw_event": payload,
                    "screening_matches": screening_matches,
                    "event_id": str(event.id)  # Internal tracking
                }
                screened_payloads.append(auditor_state)

                # Mark as processing so we don't pick it up again
                await uow.raw_events.update_status(str(event.id), "processing")
                
            await uow.commit()

        try:
            await anext(uow_gen)
        except StopAsyncIteration:
            pass

        return screened_payloads

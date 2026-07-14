from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.infrastructure.database import get_db_session
from app.infrastructure.llm_gateway import LLMGateway
from app.infrastructure.vector_store import VectorStore
from app.infrastructure.uow import SQLAlchemyUnitOfWork
from app.infrastructure.cache import InMemoryCacheProvider
from app.infrastructure.broker import AsyncioMessageBroker
from app.infrastructure.secrets import EnvSecretsManager
from app.domain.interfaces import IUnitOfWork, ICacheProvider, IMessageBroker, ISecretsManager

from app.adapters.ofac_adapter import OfacAdapter
from app.adapters.opensanctions_adapter import OpenSanctionsAdapter
from app.adapters.inject_adapter import InjectAdapter
from app.services.ingestion.ingestion_service import IngestionService
from app.services.screening.screening_service import ScreeningService

def get_llm_gateway(settings: Settings = Depends(get_settings)) -> LLMGateway:
    api_key = getattr(settings, "google_api_key", "dummy-key")
    return LLMGateway(api_key=api_key, model=settings.gemini_model)

def get_vector_store(settings: Settings = Depends(get_settings)) -> VectorStore:
    return VectorStore(persist_dir=settings.chroma_persist_dir)

async def get_uow(session: AsyncSession = Depends(get_db_session)) -> AsyncGenerator[IUnitOfWork, None]:
    uow = SQLAlchemyUnitOfWork(session)
    yield uow

_cache = InMemoryCacheProvider()
_broker = AsyncioMessageBroker()
_secrets = EnvSecretsManager()
_inject_adapter = InjectAdapter()

def get_cache() -> ICacheProvider:
    return _cache

def get_broker() -> IMessageBroker:
    return _broker

def get_secrets() -> ISecretsManager:
    return _secrets

def get_adapters(settings: Settings = Depends(get_settings)) -> list:
    data_dir = getattr(settings, "data_dir", "./data")
    return [
        OfacAdapter(data_dir=data_dir),
        OpenSanctionsAdapter(data_dir=data_dir),
        _inject_adapter
    ]

def get_ingestion_service(
    broker: IMessageBroker = Depends(get_broker),
    adapters: list = Depends(get_adapters)
) -> IngestionService:
    # Factory to create a UOW generator
    def _uow_factory() -> AsyncGenerator[IUnitOfWork, None]:
        from app.infrastructure.database import async_session_maker
        async def _gen():
            async with async_session_maker() as session:
                yield SQLAlchemyUnitOfWork(session)
        return _gen()
        
    return IngestionService(uow_factory=_uow_factory, broker=broker, adapters=adapters)

def get_screening_service(
    cache: ICacheProvider = Depends(get_cache)
) -> ScreeningService:
    def _uow_factory() -> AsyncGenerator[IUnitOfWork, None]:
        from app.infrastructure.database import async_session_maker
        async def _gen():
            async with async_session_maker() as session:
                yield SQLAlchemyUnitOfWork(session)
        return _gen()

    return ScreeningService(uow_factory=_uow_factory, cache=cache)

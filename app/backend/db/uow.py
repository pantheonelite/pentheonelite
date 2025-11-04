"""Unit of work is used for accessing to multiple repositories in as single database transaction."""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Generic, overload

from app.backend.db.models import (
    AgentDebate,
    ApiKey,
    Council,
    CouncilPerformance,
    CouncilRun,
    CouncilRunCycle,
    HedgeFundFlow,
    HedgeFundFlowRun,
    HedgeFundFlowRunCycle,
    MarketOrder,
    PortfolioHolding,
    Wallet,
)
from app.backend.db.repositories.api_key_repository import ApiKeyRepository
from app.backend.db.repositories.base_repository import AbstractSqlRepository, ModelType
from app.backend.db.repositories.council_repository import CouncilRepository
from app.backend.db.repositories.flow_repository import FlowRepository
from app.backend.db.repositories.flow_run_cycle_repository import FlowRunCycleRepository
from app.backend.db.repositories.flow_run_repository import FlowRunRepository
from app.backend.db.repositories.wallet_repository import WalletRepository
from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork(Generic[ModelType]):
    """Unit of work."""

    repository_classes: Mapping[str, type[AbstractSqlRepository]] = MappingProxyType(
        {
            HedgeFundFlow.__name__: FlowRepository,
            HedgeFundFlowRun.__name__: FlowRunRepository,
            HedgeFundFlowRunCycle.__name__: FlowRunCycleRepository,
            ApiKey.__name__: ApiKeyRepository,
            # Councils domain - use CouncilRepository only for Council
            Council.__name__: CouncilRepository,
            Wallet.__name__: WalletRepository,
        },
    )

    # Models that use generic AbstractSqlRepository with their model type
    generic_models: Mapping[str, type] = MappingProxyType(
        {
            AgentDebate.__name__: AgentDebate,
            MarketOrder.__name__: MarketOrder,
            CouncilPerformance.__name__: CouncilPerformance,
            PortfolioHolding.__name__: PortfolioHolding,
            CouncilRun.__name__: CouncilRun,
            CouncilRunCycle.__name__: CouncilRunCycle,
        },
    )

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repositories: dict[str, AbstractSqlRepository] = {}

    async def __aenter__(self) -> "UnitOfWork":
        """Prepare repositories before entering the context."""
        # Create specific repositories
        for model_name, klass in self.repository_classes.items():
            self.repositories[model_name] = klass(self.session)

        # Create generic repositories with model type
        for model_name, model_class in self.generic_models.items():
            self.repositories[model_name] = AbstractSqlRepository(self.session, model_class)

        return self

    async def __aexit__(self, *args):
        """Clean up before exiting the context."""
        await self.session.close()

    def add(self, instance: ModelType) -> None:
        """
        Support function for insert/update into database.

        Parameters
        ----------
        instance : BaseModel
            model instance

        """
        self.session.add(instance)

    async def commit(self):
        """Commit changes to database."""
        await self.session.commit()

    async def rollback(self):
        """Rollback changes from database."""
        await self.session.rollback()

    # Specific repository overloads
    @overload
    def get_repository(self, model: type[HedgeFundFlow]) -> FlowRepository: ...

    @overload
    def get_repository(self, model: type[HedgeFundFlowRun]) -> FlowRunRepository: ...

    @overload
    def get_repository(self, model: type[HedgeFundFlowRunCycle]) -> FlowRunCycleRepository: ...

    @overload
    def get_repository(self, model: type[ApiKey]) -> ApiKeyRepository: ...

    @overload
    def get_repository(self, model: type[Council]) -> CouncilRepository: ...

    @overload
    def get_repository(self, model: type[Wallet]) -> WalletRepository: ...

    # Generic repository overloads
    @overload
    def get_repository(self, model: type[AgentDebate]) -> AbstractSqlRepository[AgentDebate]: ...

    @overload
    def get_repository(self, model: type[MarketOrder]) -> AbstractSqlRepository[MarketOrder]: ...

    @overload
    def get_repository(self, model: type[CouncilPerformance]) -> AbstractSqlRepository[CouncilPerformance]: ...

    @overload
    def get_repository(self, model: type[PortfolioHolding]) -> AbstractSqlRepository[PortfolioHolding]: ...

    @overload
    def get_repository(self, model: type[CouncilRun]) -> AbstractSqlRepository[CouncilRun]: ...

    @overload
    def get_repository(self, model: type[CouncilRunCycle]) -> AbstractSqlRepository[CouncilRunCycle]: ...

    def get_repository(self, model: type[ModelType]) -> AbstractSqlRepository[ModelType]:
        """
        Get repository for a given model.

        Parameters
        ----------
        model : type[ModelType]
            Model class

        Returns
        -------
        AbstractSqlRepository[ModelType]
            Repository instance for the model

        Raises
        ------
        ValueError
            If repository for the model does not exist

        """
        repo = self.repositories.get(model.__name__)
        if repo is None:
            raise ValueError(f"Repository <{model.__name__}> does not exists.")
        return repo  # type: ignore[return-value]

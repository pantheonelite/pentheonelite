"""Repository for HedgeFundFlow operations."""

from typing import Any

from app.backend.db.models import HedgeFundFlow
from app.backend.db.repositories.base_repository import AbstractSqlRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class FlowRepository(AbstractSqlRepository[HedgeFundFlow]):
    """Repository for HedgeFundFlow CRUD operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize the FlowRepository.

        Parameters
        ----------
        session : AsyncSession
            Database session for operations.
        """
        super().__init__(session, HedgeFundFlow)

    async def create_flow(
        self,
        name: str,
        nodes: dict,
        edges: dict,
        description: str | None = None,
        viewport: dict | None = None,
        data: dict | None = None,
        *,
        is_template: bool = False,
        tags: list[str] | None = None,
    ) -> HedgeFundFlow:
        """
        Create a new hedge fund flow.

        Parameters
        ----------
        name : str
            Flow name.
        nodes : dict
            Flow nodes configuration.
        edges : dict
            Flow edges configuration.
        description : str | None, optional
            Flow description, by default None.
        viewport : dict | None, optional
            Flow viewport configuration, by default None.
        data : dict | None, optional
            Additional flow data, by default None.
        is_template : bool, optional
            Whether this is a template flow, by default False.
        tags : list[str] | None, optional
            Flow tags, by default None.

        Returns
        -------
        HedgeFundFlow
            Created flow instance.
        """
        return await self.create(
            name=name,
            description=description,
            nodes=nodes,
            edges=edges,
            viewport=viewport,
            data=data,
            is_template=is_template,
            tags=tags or [],
        )

    async def get_flows_by_name(self, name: str) -> list[HedgeFundFlow]:
        """
        Get flows by name pattern.

        Parameters
        ----------
        name : str
            Name pattern to search for.

        Returns
        -------
        list[HedgeFundFlow]
            List of matching flows.
        """
        # Use __table__.c for SQLAlchemy column operations like ilike() and desc()
        stmt = (
            select(HedgeFundFlow)
            .where(HedgeFundFlow.__table__.c.name.ilike(f"%{name}%"))
            .order_by(HedgeFundFlow.__table__.c.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_template_flows(self) -> list[HedgeFundFlow]:
        """
        Get all template flows.

        Returns
        -------
        list[HedgeFundFlow]
            List of template flows.
        """
        # Use find_by which handles attribute access internally
        return await self.find_by(is_template=True)

    async def get_user_flows(self) -> list[HedgeFundFlow]:
        """
        Get all user-created flows (non-templates).

        Returns
        -------
        list[HedgeFundFlow]
            List of user flows.
        """
        # Use find_by which handles attribute access internally
        return await self.find_by(is_template=False)

    async def get_all_flows(self, *, include_templates: bool = True) -> list[HedgeFundFlow]:
        """
        Get all flows, optionally filtering by template status.

        Parameters
        ----------
        include_templates : bool, optional
            Whether to include template flows, by default True.

        Returns
        -------
        list[HedgeFundFlow]
            List of flows based on filter criteria.
        """
        if include_templates:
            # Use __table__.c for SQLAlchemy column operations
            stmt = select(HedgeFundFlow).order_by(HedgeFundFlow.__table__.c.updated_at.desc())
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        return await self.get_user_flows()

    async def get_flow_by_id(self, flow_id: int) -> HedgeFundFlow | None:
        """
        Get a flow by its ID.

        Parameters
        ----------
        flow_id : int
            Flow ID to retrieve.

        Returns
        -------
        HedgeFundFlow | None
            Flow instance if found, None otherwise.
        """
        # Delegate to base repository method
        return await self.get_by_id(flow_id)

    async def delete_flow(self, flow_id: int) -> bool:
        """
        Delete a flow by its ID.

        Parameters
        ----------
        flow_id : int
            Flow ID to delete.

        Returns
        -------
        bool
            True if deleted successfully, False if not found.
        """
        # Delegate to base repository method
        return await self.delete(flow_id)

    async def update_flow(
        self,
        flow_id: int,
        name: str | None = None,
        description: str | None = None,
        nodes: dict | None = None,
        edges: dict | None = None,
        viewport: dict | None = None,
        data: dict | None = None,
        *,
        is_template: bool | None = None,
        tags: list[str] | None = None,
    ) -> HedgeFundFlow | None:
        """
        Update an existing flow.

        Parameters
        ----------
        flow_id : int
            Flow ID to update.
        name : str | None, optional
            New name, by default None.
        description : str | None, optional
            New description, by default None.
        nodes : dict | None, optional
            New nodes configuration, by default None.
        edges : dict | None, optional
            New edges configuration, by default None.
        viewport : dict | None, optional
            New viewport configuration, by default None.
        data : dict | None, optional
            New data, by default None.
        is_template : bool | None, optional
            New template status, by default None.
        tags : list[str] | None, optional
            New tags, by default None.

        Returns
        -------
        HedgeFundFlow | None
            Updated flow if found, None otherwise.
        """
        update_data: dict[str, Any] = {}

        # Build update dictionary with only non-None values
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if nodes is not None:
            update_data["nodes"] = nodes
        if edges is not None:
            update_data["edges"] = edges
        if viewport is not None:
            update_data["viewport"] = viewport
        if data is not None:
            update_data["data"] = data
        if is_template is not None:
            update_data["is_template"] = is_template
        if tags is not None:
            update_data["tags"] = tags

        # Delegate to base repository method
        return await self.update(flow_id, **update_data)

    async def duplicate_flow(self, flow_id: int, *, new_name: str | None = None) -> HedgeFundFlow | None:
        """
        Duplicate an existing flow.

        Parameters
        ----------
        flow_id : int
            Flow ID to duplicate.
        new_name : str | None, optional
            Name for the duplicate, by default None.

        Returns
        -------
        HedgeFundFlow | None
            Duplicated flow if original found, None otherwise.
        """
        # Get the original flow
        original = await self.get_by_id(flow_id)
        if not original:
            return None

        # Create a copy with modified name
        # Note: Accessing instance attributes (original.name, etc.) is safe
        copy_name = new_name or f"{original.name} (Copy)"
        return await self.create_flow(
            name=copy_name,
            description=original.description,
            nodes=original.nodes,
            edges=original.edges,
            viewport=original.viewport,
            data=original.data,
            is_template=False,  # Duplicates are never templates
            tags=original.tags,
        )

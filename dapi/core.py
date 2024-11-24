from typing import Dict, Type, TypeVar, Any, Optional
from abc import ABC
from tapipy.tapis import Tapis
from . import auth

T = TypeVar("T", bound="BaseComponent")


class BaseComponent(ABC):
    """Base class for all DesignSafe API components."""

    def __init__(self, api: "DesignSafeAPI") -> None:
        """Initialize the component.

        Args:
            api: Parent DesignSafe API instance
        """
        self._api = api

    @property
    def tapis(self) -> Tapis:
        """Get the authenticated Tapis client."""
        return self._api.tapis


class ComponentRegistry:
    """Registry for API components."""

    def __init__(self) -> None:
        self._components: Dict[str, Type[BaseComponent]] = {}

    def register(self, name: str, component: Type[BaseComponent]) -> None:
        """Register a new component.

        Args:
            name: Name to register the component under
            component: Component class to register
        """
        self._components[name] = component

    def get(self, name: str) -> Optional[Type[BaseComponent]]:
        """Get a registered component by name.

        Args:
            name: Name of component to retrieve

        Returns:
            Component class if found, None otherwise
        """
        return self._components.get(name)

    def create(self, name: str, api: "DesignSafeAPI") -> BaseComponent:
        """Create an instance of a registered component.

        Args:
            name: Name of component to create
            api: Parent API instance to pass to component

        Returns:
            Instantiated component

        Raises:
            ValueError: If component name is not registered
        """
        component_class = self.get(name)
        if not component_class:
            raise ValueError(f"No component registered with name: {name}")
        return component_class(api)


class DesignSafeAPI:
    """Main client for interacting with DesignSafe's Tapis v3 services."""

    def __init__(self) -> None:
        """Initialize the DesignSafe API client."""
        # Initialize Tapis client using existing auth module
        self._tapis = auth.init()

        # Initialize component registry
        self._registry = ComponentRegistry()
        self._components: Dict[str, BaseComponent] = {}

        # Register default components
        self._register_default_components()

    def _register_default_components(self) -> None:
        """Register the default API components."""
        # Import components here to avoid circular imports
        from .components.jobs import JobsComponent
        from .components.files import FilesComponent

        self._registry.register("jobs", JobsComponent)
        self._registry.register("files", FilesComponent)

    @property
    def tapis(self) -> Tapis:
        """Get the authenticated Tapis client.

        Returns:
            Authenticated Tapis client instance
        """
        return self._tapis

    def register_component(self, name: str, component: Type[BaseComponent]) -> None:
        """Register a new component.

        Args:
            name: Name to register the component under
            component: Component class to register

        Raises:
            TypeError: If component is not a subclass of BaseComponent
        """
        if not issubclass(component, BaseComponent):
            raise TypeError("Component must be a subclass of BaseComponent")
        self._registry.register(name, component)

    def __getattr__(self, name: str) -> Any:
        """Provide access to registered components as properties.

        This allows components to be accessed as: api.component_name

        Args:
            name: Name of component to access

        Returns:
            Component instance

        Raises:
            AttributeError: If component name is not registered
        """
        if name not in self._components:
            try:
                self._components[name] = self._registry.create(name, self)
            except ValueError as e:
                raise AttributeError(
                    f"'{self.__class__.__name__}' has no attribute '{name}'"
                ) from e

        return self._components[name]

"""Template manager initialization and utilities."""

import threading
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from src.core.config import get_settings

from .email_templates import EmailTemplateManager

settings = get_settings()


class TemplateManager:
    """Central template manager that can load templates from multiple directories.

    This class follows the singleton pattern to ensure only one instance exists.
    """

    _instance = None
    _initialized = False
    _lock = threading.Lock()

    def __new__(cls):
        """Create a new instance if one doesn't exist.

        Returns:
            The singleton instance of TemplateManager
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the template manager if not already initialized."""
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._managers: List[EmailTemplateManager] = []
                    self._default_manager: Optional[EmailTemplateManager] = None
                    self._initialized = True

    def add_template_dir(self, template_dir: str, is_default: bool = False) -> None:
        """Add a template directory to search for templates.

        Args:
            template_dir: Path to the template directory
            is_default: If True, this will be the default directory for template lookups
        """
        manager = EmailTemplateManager(str(Path(template_dir).resolve()))
        self._managers.insert(0, manager)  # Newer directories take precedence
        if is_default or not self._default_manager:
            self._default_manager = manager

    @lru_cache(maxsize=32)
    def get_template(self, template_name: str) -> str:
        """Get template content from the first matching template directory.

        Args:
            template_name: Name of the template file to find

        Returns:
            Rendered template content

        Raises:
            FileNotFoundError: If template is not found in any directory
        """
        for manager in self._managers:
            try:
                return manager.render_template(template_name, {})
            except ValueError:
                continue
        raise FileNotFoundError(
            f"Template '{template_name}' not found in any template directory"
        )

    def render_template(self, template_name: str, context: dict) -> str:
        """Render a template with the given context.

        Args:
            template_name: Name of the template file
            context: Dictionary of variables to pass to the template

        Returns:
            Rendered template as string

        Raises:
            FileNotFoundError: If template is not found in any directory
            ValueError: If template rendering fails
        """
        if not self._default_manager:
            raise RuntimeError("No template directories configured")

        return self._default_manager.render_template(template_name, context)


def setup_template_manager() -> TemplateManager:
    """Initialize and configure the template manager.

    Template loading order:
    1. Domain-specific templates (highest priority)
    2. Base templates (from core/templating/base_templates)
    3. Default templates (lowest priority, from settings)
    """
    manager = TemplateManager()

    # 1. Add domain-specific templates (highest priority)
    domain_templates_dir = (
        Path(__file__).parent.parent / "users" / "domain" / "templates"
    )
    if domain_templates_dir.exists():
        manager.add_template_dir(str(domain_templates_dir), is_default=False)

    # 2. Add base templates from core
    base_templates_dir = Path(settings.BASE_TEMPLATE_DIR).resolve()
    if base_templates_dir.exists():
        manager.add_template_dir(str(base_templates_dir), is_default=True)

    return manager


# Initialize the global template manager
template_manager = setup_template_manager()

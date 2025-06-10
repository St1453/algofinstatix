import threading
from functools import lru_cache
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape


class EmailTemplateManager:
    _instance = None
    _initialized = False
    _lock = threading.Lock()

    def __new__(cls, template_dir: str) -> "EmailTemplateManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, template_dir: str) -> None:
        """Initialize the template manager with caching.

        Args:
            template_dir: Directory containing the email templates
        """
        if not self._initialized:
            self.template_dir = template_dir
            self.env = Environment(
                loader=FileSystemLoader(template_dir),
                autoescape=select_autoescape(["html", "xml"]),
                trim_blocks=True,
                lstrip_blocks=True,
            )
            self._template_cache: Dict[str, Template] = {}
            self._initialized = True

    @lru_cache(maxsize=32)
    def _get_template(self, template_name: str) -> Optional[Template]:
        """Get a template from cache or load it if not cached.

        Args:
            template_name: Name of the template file

        Returns:
            The loaded template or None if not found
        """
        try:
            return self.env.get_template(template_name)
        except Exception:
            return None

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a template with the given context.

        Args:
            template_name: Name of the template file
            context: Dictionary of variables to pass to the template

        Returns:
            Rendered template as a string

        Raises:
            ValueError: If template loading fails
        """
        # Get template from cache or load it
        template = self._get_template(template_name)
        if template is None:
            raise ValueError(f"Template {template_name} not found or invalid")

        try:
            return template.render(**context)
        except Exception as e:
            raise ValueError(f"Failed to render template: {str(e)}") from e

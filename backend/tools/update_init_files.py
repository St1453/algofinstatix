"""Script to update all __init__.py files in the project with proper structure."""
import os
from pathlib import Path


def update_init_files(root_dir: str):
    """Update all __init__.py files in the project."""
    for root, dirs, files in os.walk(root_dir):
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")

        if "__init__.py" in files:
            init_path = Path(root) / "__init__.py"
            rel_path = Path(root).relative_to(root_dir)
            package_name = rel_path.name
            parent_package = rel_path.parent.name

            # Skip if already has content
            with open(init_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content and not content.startswith('"""' * 3):
                    continue

            # Choose template based on directory
            if "domain" in str(rel_path):
                template = DOMAIN_TEMPLATE.format(package_name=package_name)
            elif "infrastructure" in str(rel_path) or "infra" in str(rel_path):
                template = INFRA_TEMPLATE.format(package_name=package_name)
            else:
                template = DEFAULT_TEMPLATE.format(package_name=package_name)

            # Write the template
            with open(init_path, "w", encoding="utf-8") as f:
                f.write(template)
            print(f"Updated: {init_path}")


if __name__ == "__main__":
    # Define templates
    DOMAIN_TEMPLATE = '''"""{package_name} domain package.

This package contains domain models, interfaces, and services
for the {package_name} domain.
"""
from __future__ import annotations

__all__ = [
    # Add public API here
]

# Initialize package-level logger
import logging

logger = logging.getLogger(__name__)'''

    INFRA_TEMPLATE = '''"""{package_name} infrastructure package.

This package contains infrastructure implementations for the {package_name} domain,
including repositories, services, and external service adapters.
"""
from __future__ import annotations

__all__ = [
    # Add public API here
]

# Initialize package-level logger
import logging

logger = logging.getLogger(__name__)'''

    DEFAULT_TEMPLATE = '''"""{package_name} package.

This package contains components for the {package_name} module.
"""
from __future__ import annotations

__all__ = [
    # Add public API here
]

# Initialize package-level logger
import logging

logger = logging.getLogger(__name__)'''

    # Run the updater
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src_dir = os.path.join(project_root, "src")
    update_init_files(src_dir)

"""Factory for creating user roles with predefined permission sets."""

from .policies import Permission, UserRole


class UserRoleFactory:
    """Factory class for creating predefined user roles with associated permissions.

    This factory provides static methods to create standard user roles with predefined
    permission sets, ensuring consistency across the application.
    """

    @staticmethod
    def user() -> UserRole:
        """Create a standard user role with basic permissions.

        Standard users can manage their own account but cannot access other users' data.

        Returns:
            UserRole: A UserRole instance with standard user permissions
        """
        return UserRole(
            "user",
            {
                Permission.READ_OWN,
                Permission.UPDATE_OWN,
                Permission.DELETE_OWN,
            },
        )

    @staticmethod
    def admin() -> UserRole:
        """Create an admin role with full permissions.

        Admin users have full access to all user management features.

        Returns:
            UserRole: A UserRole instance with admin permissions
        """
        return UserRole(
            "admin",
            {
                Permission.READ_OWN,
                Permission.UPDATE_OWN,
                Permission.DELETE_OWN,
                Permission.READ_ANY,
                Permission.UPDATE_ANY,
                Permission.DELETE_ANY,
                Permission.CREATE_ACCOUNT_FULL,
            },
        )

    @staticmethod
    def get_role(role_name: str) -> UserRole:
        """Get a role by name.
        
        Args:
            role_name: Name of the role to retrieve (e.g., 'user', 'admin')
            
        Returns:
            UserRole: The corresponding UserRole instance
            
        Raises:
            ValueError: If the role name is not recognized
            
        Example:
            >>> role = UserRoleFactory.get_role('admin')
            >>> role.name
            'admin'
        """
        role_creators = {
            'user': UserRoleFactory.user,
            'admin': UserRoleFactory.admin,
        }
        
        if role_name not in role_creators:
            raise ValueError(f"Unknown role: {role_name}")
            
        return role_creators[role_name]()

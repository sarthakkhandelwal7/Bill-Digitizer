# This file makes the 'crud' directory a Python package.
from .crud_bill import bill
from .crud_user import CRUDUser

# Export a user instance for consistency with bill
from app.db.models.user import User as UserModel
user = CRUDUser(UserModel) 
import uuid
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db

role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permissions.id"), primary_key=True),
)


class Permission(db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(200))

    def __repr__(self):
        return f"<Permission {self.code}>"


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(200))

    permissions = db.relationship(
        "Permission", secondary=role_permissions, backref="roles", lazy="joined"
    )
    users = db.relationship("User", backref="role", lazy=True)

    def has_permission(self, code: str) -> bool:
        return any(p.code == code for p in self.permissions)

    def __repr__(self):
        return f"<Role {self.name}>"


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))

    users = db.relationship("User", backref="department", lazy=True)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, index=True, default=lambda: uuid.uuid4().hex)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)

    is_active_user = db.Column("is_active", db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    documents = db.relationship("Document", backref="uploaded_by", lazy=True,
                                 foreign_keys="Document.uploaded_by_id")
    requests_made = db.relationship("ServiceRequest", backref="requester", lazy=True,
                                     foreign_keys="ServiceRequest.requester_id")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return self.is_active_user

    def has_permission(self, code: str) -> bool:
        return self.role.has_permission(code) if self.role else False

    def __repr__(self):
        return f"<User {self.username} ({self.role.name if self.role else 's/rol'})>"


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, index=True, default=lambda: uuid.uuid4().hex)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(80), default="General")

    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    is_public = db.Column(db.Boolean, default=True)

    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    department = db.relationship("Department")


class RequestType(db.Model):
    __tablename__ = "request_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)

    department = db.relationship("Department")


class ServiceRequest(db.Model):
    __tablename__ = "service_requests"

    ESTADOS = ["Pendiente", "En proceso", "Aprobada", "Rechazada", "Cancelada"]

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, index=True, default=lambda: uuid.uuid4().hex)
    folio = db.Column(db.String(20), unique=True, nullable=False)
    request_type_id = db.Column(db.Integer, db.ForeignKey("request_types.id"), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="Pendiente", nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    request_type = db.relationship("RequestType")
    assigned_to = db.relationship("User", foreign_keys=[assigned_to_id])
    comments = db.relationship("RequestComment", backref="service_request",
                                lazy=True, order_by="RequestComment.created_at",
                                cascade="all, delete-orphan")


class RequestComment(db.Model):
    __tablename__ = "request_comments"

    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey("service_requests.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    new_status = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")

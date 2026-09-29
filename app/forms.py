from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (
    StringField, PasswordField, SelectField, TextAreaField,
    BooleanField, SubmitField,
)
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional


class LoginForm(FlaskForm):
    username = StringField("Usuario", validators=[DataRequired(), Length(max=64)])
    password = PasswordField("Contraseña", validators=[DataRequired()])
    remember_me = BooleanField("Recordarme")
    submit = SubmitField("Iniciar sesión")


class UserForm(FlaskForm):
    username = StringField("Usuario", validators=[DataRequired(), Length(max=64)])
    full_name = StringField("Nombre completo", validators=[DataRequired(), Length(max=150)])
    email = StringField("Correo electrónico", validators=[DataRequired(), Email(check_deliverability=False)])
    role_id = SelectField("Perfil (rol)", coerce=int, validators=[DataRequired()])
    department_id = SelectField("Departamento", coerce=int, validators=[Optional()])
    password = PasswordField(
        "Contraseña",
        validators=[Optional(), Length(min=6, message="Mínimo 6 caracteres")],
    )
    confirm_password = PasswordField(
        "Confirmar contraseña",
        validators=[EqualTo("password", message="Las contraseñas no coinciden")],
    )
    is_active_user = BooleanField("Usuario activo", default=True)
    submit = SubmitField("Guardar")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Contraseña actual", validators=[DataRequired()])
    new_password = PasswordField("Nueva contraseña", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirmar nueva contraseña",
        validators=[DataRequired(), EqualTo("new_password", message="Las contraseñas no coinciden")],
    )
    submit = SubmitField("Actualizar contraseña")


class DocumentForm(FlaskForm):
    title = StringField("Título", validators=[DataRequired(), Length(max=150)])
    description = TextAreaField("Descripción", validators=[Optional(), Length(max=1000)])
    category = StringField("Categoría", validators=[Optional(), Length(max=80)])
    department_id = SelectField("Departamento", coerce=int, validators=[Optional()])
    is_public = BooleanField("Visible para todos los colaboradores", default=True)
    file = FileField(
        "Archivo",
        validators=[
            FileRequired(message="Debes seleccionar un archivo"),
            FileAllowed(
                ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "png", "jpg", "jpeg", "txt", "csv"],
                message="Formato de archivo no permitido",
            ),
        ],
    )
    submit = SubmitField("Subir documento")


class ServiceRequestForm(FlaskForm):
    request_type_id = SelectField("Tipo de solicitud", coerce=int, validators=[DataRequired()])
    description = TextAreaField(
        "Descripción / detalle de tu solicitud",
        validators=[DataRequired(), Length(max=2000)],
    )
    submit = SubmitField("Enviar solicitud")


class RequestUpdateForm(FlaskForm):
    status = SelectField(
        "Nuevo estado",
        choices=[(s, s) for s in ["Pendiente", "En proceso", "Aprobada", "Rechazada", "Cancelada"]],
        validators=[DataRequired()],
    )
    assigned_to_id = SelectField("Asignar a", coerce=int, validators=[Optional()])
    comment = TextAreaField("Comentario", validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField("Actualizar solicitud")


class RoleForm(FlaskForm):
    name = StringField("Nombre del rol", validators=[DataRequired(), Length(max=64)])
    description = StringField("Descripción", validators=[Optional(), Length(max=200)])
    submit = SubmitField("Guardar rol")


class DepartmentForm(FlaskForm):
    name = StringField("Nombre del departamento", validators=[DataRequired(), Length(max=100)])
    description = StringField("Descripción", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Guardar departamento")

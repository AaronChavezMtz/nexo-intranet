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
    username = StringField(
        "Usuario",
        validators=[DataRequired(message="El usuario es obligatorio."), Length(min=3, max=64)],
    )
    full_name = StringField(
        "Nombre completo",
        validators=[DataRequired(message="El nombre es obligatorio."), Length(min=3, max=150)],
    )
    email = StringField(
        "Correo electrónico",
        validators=[
            DataRequired(message="El correo es obligatorio."),
            # check_deliverability=False: en una intranet los correos suelen usar
            # dominios internos (.local, .corp) que no tienen registro DNS público.
            Email(check_deliverability=False, message="Ingresa un correo válido."),
        ],
    )
    role_id = SelectField(
        "Perfil (rol)", coerce=int,
        validators=[DataRequired(message="Selecciona un perfil.")],
    )
    department_id = SelectField("Departamento", coerce=int, validators=[Optional()])
    password = PasswordField(
        "Contraseña",
        validators=[Optional(), Length(min=6, message="Mínimo 6 caracteres")],
        render_kw={"autocomplete": "new-password"},
    )
    confirm_password = PasswordField(
        "Confirmar contraseña",
        validators=[EqualTo("password", message="Las contraseñas no coinciden")],
        render_kw={"autocomplete": "new-password"},
    )
    is_active_user = BooleanField("Usuario activo", default=True)
    submit = SubmitField("Guardar")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(
        "Contraseña actual", validators=[DataRequired()],
        render_kw={"autocomplete": "current-password"},
    )
    new_password = PasswordField(
        "Nueva contraseña", validators=[DataRequired(), Length(min=6)],
        render_kw={"autocomplete": "new-password"},
    )
    confirm_password = PasswordField(
        "Confirmar nueva contraseña",
        validators=[DataRequired(), EqualTo("new_password", message="Las contraseñas no coinciden")],
        render_kw={"autocomplete": "new-password"},
    )
    submit = SubmitField("Actualizar contraseña")


class DocumentForm(FlaskForm):
    title = StringField(
        "Título",
        validators=[DataRequired(message="El título es obligatorio."), Length(min=3, max=150)],
    )
    description = TextAreaField(
        "Descripción",
        validators=[Optional(), Length(max=1000, message="Máximo 1000 caracteres.")],
    )
    category = StringField(
        "Categoría",
        validators=[Optional(), Length(max=80, message="Máximo 80 caracteres.")],
    )
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
        validators=[DataRequired(message="Describe tu solicitud."), Length(min=10, max=2000)],
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
    name = StringField(
        "Nombre del departamento",
        validators=[
            DataRequired(message="El nombre es obligatorio."),
            Length(min=3, max=100, message="Debe tener entre 3 y 100 caracteres."),
        ],
    )
    description = StringField(
        "Descripción",
        validators=[Optional(), Length(max=255, message="Máximo 255 caracteres.")],
    )
    submit = SubmitField("Guardar departamento")
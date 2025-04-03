from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField
from wtforms.validators import DataRequired, URL

class VideoSourceForm(FlaskForm):
    name = StringField('Nombre del video', validators=[DataRequired()])
    video_url = StringField('URL del video', validators=[DataRequired(), URL()])
    is_active = BooleanField('Activar este video')
    submit = SubmitField('Guardar')
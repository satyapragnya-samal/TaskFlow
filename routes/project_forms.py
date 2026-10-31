from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

class ProjectForm(FlaskForm):
    title = StringField('Project Title', validators=[
        DataRequired(message="Project title is required."),
        Length(min=3, max=150, message="Title must be between 3 and 150 characters.")
    ])
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=1000, message="Description must be under 1000 characters.")
    ])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[Optional()])
    deadline = DateField('Target Deadline', validators=[Optional()])
    submit = SubmitField('Save Project')


class AddMemberForm(FlaskForm):
    username_or_email = StringField('Username or Email Address', validators=[
        DataRequired(message="Enter a valid username or email to add.")
    ])
    submit = SubmitField('Add Member')
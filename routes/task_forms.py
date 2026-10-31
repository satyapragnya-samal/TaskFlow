from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

class TaskForm(FlaskForm):
    title = StringField('Task Title', validators=[
        DataRequired(message="Task title is required."),
        Length(min=3, max=200, message="Title must be between 3 and 200 characters.")
    ])
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=2000, message="Description must be under 2000 characters.")
    ])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('in_review', 'In Review'),
        ('completed', 'Completed')
    ], default='todo', validators=[DataRequired()])
    assignee_id = SelectField('Assignee', coerce=int, validators=[Optional()])
    due_date = DateField('Due Date', validators=[Optional()])
    submit = SubmitField('Save Task')


class CommentForm(FlaskForm):
    content = TextAreaField('Add a comment', validators=[
        DataRequired(message="Comment cannot be blank."),
        Length(max=1000, message="Comment is too long.")
    ])
    submit = SubmitField('Post Comment')
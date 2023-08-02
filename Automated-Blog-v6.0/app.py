from website import create_app

app, celery = create_app()

from website.models import User
from website import db

app.app_context().push()


if __name__ == '__main__':
    app.run(debug=True)
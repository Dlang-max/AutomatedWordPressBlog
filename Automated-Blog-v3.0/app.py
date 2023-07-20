from website import create_app
from datetime import timedelta

app = create_app()

if __name__ == '__main__':
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
    app.run(debug=True)

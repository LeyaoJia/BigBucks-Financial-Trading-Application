import os
import click
from flask import Flask

def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "bigbucks.sqlite"),
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.update(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route("/hello")
    def hello():
        return "Hello, World!"

    # Initialize database functionalities
    from Bigbucks.db import init_app as initialize_database
    initialize_database(app)

    # Register the CLI command for initializing the database
    # app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

    # Register blueprints
    from . import auth, member, administrator
    app.register_blueprint(auth.bp)  # auth is the login/register part
    app.register_blueprint(member.bp)  # Now member just provides a blank index page
    app.register_blueprint(administrator.bp)

    app.add_url_rule("/", endpoint="index")

    return app

@click.command("init-db")
def init_db_command():
    """Clear existing data and create new tables."""
    from .db import init_db  # Ensure db is imported locally to avoid circular imports
    init_db()
    click.echo("Initialized the database.")

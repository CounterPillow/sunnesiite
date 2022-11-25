from flask import Flask
import toml


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_file("config.toml", load=toml.load)

    from . import main

    app.register_blueprint(main.bp, url_prefix=app.config["SUNNESIITE_PREFIX"])

    return app

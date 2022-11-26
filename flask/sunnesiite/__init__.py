from flask import Flask
from flask_caching import Cache
import toml


cache = Cache()


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_file("config.toml", load=toml.load)

    from . import main

    app.register_blueprint(main.bp, url_prefix=app.config["SUNNESIITE_PREFIX"])

    # Flask-Caching
    cache.init_app(app, config=app.config)

    return app

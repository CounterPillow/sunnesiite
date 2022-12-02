from flask import Flask
from flask_caching import Cache
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


cache = Cache()


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # Can't use from_file with tomllib.load here because it wants it opened in
    # rb mode for utf-8 and line ending reasons
    with app.open_instance_resource("config.toml", mode="rb") as cf:
        conf = tomllib.load(cf)
    app.config.from_mapping(conf)

    from . import main

    app.register_blueprint(main.bp, url_prefix=app.config["SUNNESIITE_PREFIX"])

    # Flask-Caching
    cache.init_app(app, config=app.config)

    return app

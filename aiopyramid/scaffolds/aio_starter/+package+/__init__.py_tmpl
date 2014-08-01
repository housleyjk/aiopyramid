import logging.config

from pyramid.config import Configurator


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    # support logging in python3
    logging.config.fileConfig(
        settings['logging.config'],
        disable_existing_loggers=False
    )

    config = Configurator(settings=settings)
    config.add_route('say_hello', '/')
    config.scan()
    return config.make_wsgi_app()

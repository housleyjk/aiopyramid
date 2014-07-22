from pyramid.scaffolds import PyramidTemplate


class AioJinja2Template(PyramidTemplate):
    _template_dir = 'aio_jinja2'
    summary = 'Pyramid project using asyncio and jinja2'

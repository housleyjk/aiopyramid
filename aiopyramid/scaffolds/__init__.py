from pyramid.scaffolds import PyramidTemplate


class AioJinja2Template(PyramidTemplate):
    _template_dir = 'aio_starter'
    summary = 'Pyramid project using asyncio'

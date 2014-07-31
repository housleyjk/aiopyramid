from pyramid.scaffolds import PyramidTemplate


class AioStarterTemplate(PyramidTemplate):
    _template_dir = 'aio_starter'
    summary = 'Pyramid project using asyncio'

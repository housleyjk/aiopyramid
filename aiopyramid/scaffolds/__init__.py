from pyramid.scaffolds import PyramidTemplate


class AioStarterTemplate(PyramidTemplate):
    _template_dir = 'aio_starter'
    summary = 'Pyramid project using asyncio'


class AioWebsocketTemplate(PyramidTemplate):
    _template_dir = 'aio_websocket'
    summary = 'Aiopyramid project with websocket-based view'

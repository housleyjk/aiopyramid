import venusian


class coroutine_view_config(object):
    """
    A patched version of view_config that use coroutine for views
    """
    venusian = venusian # for testing injection
    def __init__(self, **settings):
        if 'for_' in settings:
            if settings.get('context') is None:
                settings['context'] = settings['for_']
        self.__dict__.update(settings)

    def __call__(self, wrapped):
        settings = self.__dict__.copy()
        depth = settings.pop('_depth', 0)

        def callback(context, name, ob):
            config = context.config.with_package(info.module)
            config.add_coroutine_view(view=ob, **settings)

        info = self.venusian.attach(wrapped, callback, category='pyramid',
                                    depth=depth + 1)

        if info.scope == 'class':
            # if the decorator was attached to a method in a class, or
            # otherwise executed at class scope, we need to set an
            # 'attr' into the settings if one isn't already in there
            if settings.get('attr') is None:
                settings['attr'] = wrapped.__name__

        settings['_info'] = info.codeinfo # fbo "action_method"
        return wrapped

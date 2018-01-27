from aiohttp import web


async def get_all_todos(request):
    todos = await request.app['actor'].get_response('/local/state', {'action': 'get'})
    return web.json_response([
        {'id': idx, **todo} for idx, todo in enumerate(todos)
    ])


async def get_one_todo(request):
    id = int(request.match_info['id'])

    todo = await request.app['actor'].get_response('/local/state', {'action': 'get', 'id': id})

    if todo.get('error'):
        return web.json_response(todo, status=404)

    return web.json_response({'id': id, **todo})


async def kill_server(request):
    await request.app['actor'].close()
    return web.json_response(text='closed', status=200)


async def on_shutdown(app):
    print('Shutting Down!')


def app_factory(args=()):
    app = web.Application()
    app.router.add_get('/todos/', get_all_todos, name='all_todos')
    app.router.add_get('/todos/{id:\d+}', get_one_todo, name='one_todo')
    app.router.add_get('/end/', kill_server, name='kill')
    app.on_shutdown.append(on_shutdown)

    return app

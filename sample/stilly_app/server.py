from aiohttp import web


async def get_all_todos(request):
    todos = await request.app['actor'].get_response('/local/state', {'action': 'get', 'prefix': b'todos::'})
    return web.json_response([
        {'id': idx, **todo} for idx, todo in enumerate(todos)
    ])


async def get_one_todo(request):
    id = int(request.match_info['id'])
    key = b'todos::' + bytes(str(id), 'utf-8')
    todo = await request.app['actor'].get_response('/local/state', {'action': 'get', 'id': key})

    if todo.get('error'):
        return web.json_response(todo, status=404)

    return web.json_response({'id': id, **todo})


async def add_one_todo(request):
    data = await request.json()
    req = {
        'action': 'add',
        'prefix': b'todos::',
        'value': data['value'],
    }
    resp = await request.app['actor'].get_response('/local/state', req)

    if resp.get('error'):
        return web.json_response(resp, status=404)

    todo_id, todo = list(resp.items())[0]
    return web.json_response({'id': todo_id, **todo})


async def kill_server(request):
    await request.app['actor'].close()
    return web.json_response(text='closed', status=200)


async def on_shutdown(app):
    app['actor'].log('Shutting Down!')


def app_factory(args=()):
    app = web.Application()
    app.router.add_get('/todos/', get_all_todos, name='all_todos')
    app.router.add_get('/todos/{id:\d+}', get_one_todo, name='one_todo')
    app.router.add_post('/todos/new', add_one_todo, name='add_todo')
    app.router.add_get('/end/', kill_server, name='kill')
    app.on_shutdown.append(on_shutdown)

    return app

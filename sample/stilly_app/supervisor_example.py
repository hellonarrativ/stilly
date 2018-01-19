from stilly.supervisor import Supervisor
from stilly_app.server import app_factory

actor_configs = [
    ('http', 'aiohttp', {'app_factory': app_factory}),
    ('state', 'dict', {}),
]

Supervisor(actor_configs=actor_configs).run()

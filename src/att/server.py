import ipaddress
import click
import aiopg.sa
from aiohttp import web

import att.handlers as hndl


async def setup_db(app):
    engine = await aiopg.sa.create_engine(dsn=app['db_url'])
    app['db'] = engine


async def close_db(app):
    engine = app['db']
    engine.close()
    await engine.wait_closed()


def validate_ip_port(ctx, param, value):
    try:
        ip = ipaddress.ip_address(value.split(':')[0])
    except ValueError:
        raise click.BadParameter('invalid IP address')
    try:
        port = int(value.split(':')[1])
    except ValueError:
        raise click.BadParameter('port not an integer')
    except IndexError:
        raise click.BadParameter('port number not specified')
    if not 1 <= port <= 65535:
        raise click.BadParameter('port not in 1-65535 range')
    return {'host': str(ip), 'port': port}


@click.command()
@click.option('--db-url')
@click.option(
    '--listen',
    default='127.0.0.1:8000',
    callback=validate_ip_port,
    help='interface:port for listening',
)
def main(db_url, listen):
    app = web.Application()
    app['db_url'] = db_url
    app.on_startup.append(setup_db)
    app.on_cleanup.append(close_db)

    app.add_routes([
        web.post('/login', hndl.login),
        web.get('/user/{id}/groups', hndl.user_groups),
    ])

    web.run_app(app, **listen)

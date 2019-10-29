import ipaddress
import click
import aiopg.sa
import sqlalchemy as sa
from aiohttp import web

from att.db.schema import t_user


CHECK_PASSWORD = (
    sa.select([
        t_user.c.id.label('user_id'),
    ])
    .where(t_user.c.login == sa.bindparam('login'))
    .where(t_user.c.password == sa.func.crypt(sa.bindparam('password'), t_user.c.password))
)


def make_login_response(user_id):
    if user_id is not None:
        return web.json_response({'user_id': str(user_id)})
    else:
        return web.json_response({'error': 'auth failed'})


async def login(request):
    params = await request.json()
    login = params.get('login')
    password = params.get('password')

    async with request.app['db'].acquire() as conn:
        result = await conn.execute(
            CHECK_PASSWORD, login=login, password=password
        )
        user_id = await result.scalar()

    return make_login_response(user_id)


async def user_groups(request):
    user_id = request.match_info.get('id', None)
    groups = []

    # fill the gap

    return web.json_response({'groups': groups})


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
    if 1 <= port <= 65535:
        return {'host': str(ip), 'port': port}
    else:
        raise click.BadParameter('port not in 1-65535 range')

@click.command()
@click.option('--db-url')
@click.option('--listen', default='127.0.0.1:8000', callback=validate_ip_port, help='interface:port for listening')
def main(db_url, listen):
    app = web.Application()
    app['db_url'] = db_url
    app.on_startup.append(setup_db)
    app.on_cleanup.append(close_db)

    app.add_routes([
        web.post('/login', login),
        web.get('/user/{id}/groups', user_groups),
    ])

    web.run_app(app, **listen)

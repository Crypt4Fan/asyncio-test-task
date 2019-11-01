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

ADD_USER = (
    t_user.insert().values(
        login = sa.bindparam('login'),
        password = sa.func.crypt(sa.bindparam('password'), sa.func.gen_salt('bf', 8))
    )
)

GET_USER_ID = (
    sa.select([
        t_user.c.id
    ])
    .where(t_user.c.login == sa.bindparam('login'))
)


async def user_exist(login, conn):
    result = await conn.execute(
        GET_USER_ID, login=login
    )
    exist = await result.scalar()
    if exist:
        return True
    else:
        return False


async def check_signup_params(login, password, conn):
    if len(login) == 0:
        return 'login is empty'
    if login.lower() != login:
        return 'login not in lowercase'
    if len(password) == 0:
        return 'password is empty'
    if await user_exist(login, conn):
        return 'user already exists'
    return None


def make_signup_response(error, user_id):
    if error:
        return web.json_response({'error': error})
    else:
        return web.json_response({'user_id': str(user_id)})


async def signup(request):
    params = await request.json()
    login = params.get('login')
    password = params.get('password')

    user_id = None
    async with request.app['db'].acquire() as conn:
        error = await check_signup_params(login, password, conn)
        if not error:
            await conn.execute(
                ADD_USER, login=login, password=password
            )
            result = await conn.execute(
                GET_USER_ID, login=login
            )
            user_id = await result.scalar()

    return make_signup_response(error, user_id)


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

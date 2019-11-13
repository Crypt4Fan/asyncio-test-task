import asyncio
import re
import sqlalchemy as sa
from aiohttp import web

from att.db.schema import t_user, t_group, t_user_group


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

EXIST_USER = (
    sa.select([
        t_user.c.id
    ])
    .where(t_user.c.id == sa.bindparam('user_id'))
)

async def exist_user(user_id, conn):
    result = await conn.execute(
        EXIST_USER, user_id=user_id
    )
    return await result.scalar()

GET_USER_ID_BY_LOGIN = (
    sa.select([
        t_user.c.id
    ])
    .where(t_user.c.login == sa.bindparam('login'))
)

async def get_user_id_by_login(login, conn):
    result = await conn.execute(
        GET_USER_ID_BY_LOGIN, login=login
    )
    return await result.scalar()

ADD_GROUP = (t_group.insert().values(name=sa.bindparam('name')))

EXIST_GROUP = (
    sa.select([
        t_group.c.id
    ])
    .where(t_group.c.id == sa.bindparam('group_id'))
)

async def exist_group(group_id, conn):
    result = await conn.execute(
        EXIST_GROUP, group_id=group_id
    )
    return await result.scalar()

GET_GROUP_ID_BY_NAME = (
    sa.select([
        t_group.c.id
    ])
    .where(t_group.c.name == sa.bindparam('name'))
)

async def get_group_id_by_name(name, conn):
    result = await conn.execute(
        GET_GROUP_ID_BY_NAME, name=name
    )
    return await result.scalar()

CHECK_USER_IN_GROUP = (
    sa.select([
        t_user_group.c.user_id,
        t_user_group.c.group_id
    ])
    .where(t_user_group.c.user_id == sa.bindparam('user_id'))
    .where(t_user_group.c.group_id == sa.bindparam('group_id'))
)

async def check_user_in_group(user_id, group_id, conn):
    result = await conn.execute(
        CHECK_USER_IN_GROUP, user_id=user_id, group_id=group_id
    )
    return await result.first()

ADD_USER_IN_GROUP = (
    t_user_group.insert().values(
        user_id = sa.bindparam('user_id'),
        group_id = sa.bindparam('group_id')
    )
)

DEL_USER_FROM_GROUP = (
    sa.delete(t_user_group)
    .where(t_user_group.c.user_id == sa.bindparam('user_id'))
    .where(t_user_group.c.group_id == sa.bindparam('group_id'))
)

LIST_USER_GROUPS = (
    sa.select([t_group.c.name.label('group_name')]).select_from(
        t_user.join(t_user_group.join(t_group))
    )
    .where(t_user.c.id == sa.bindparam('user_id'))
)

async def get_user_groups(user_id, conn):
    result = await conn.execute(
        LIST_USER_GROUPS, user_id=user_id
    )
    return await result.fetchall()


async def check_signup_params(login, password, conn):
    if not type(login) is str:
        return 'login not a string'
    if len(login) == 0:
        return 'login is empty'
    if login.lower() != login:
        return 'login not in lowercase'
    if not type(password) is str:
        return 'password not a string'
    if len(password) == 0:
        return 'password is empty'
    if await get_user_id_by_login(login, conn) != None:
        return 'user already exists'
    return None


async def signup(request):
    params = await request.json()
    login = params.get('login', '')
    password = params.get('password', '')

    async with request.app['db'].acquire() as conn:
        error = await check_signup_params(login, password, conn)
        if error:
            msg = {'error': error}
        else:
            await conn.execute(
                ADD_USER, login=login, password=password
            )
            msg = {'user_id': str(await get_user_id_by_login(login, conn))}

    return web.json_response(msg)


def make_login_response(user_id):
    if user_id is not None:
        return web.json_response({'user_id': str(user_id)})
    else:
        return web.json_response({'error': 'auth failed'})


async def login(request):
    params = await request.json()
    login = params.get('login', '')
    password = params.get('password', '')

    async with request.app['db'].acquire() as conn:
        result = await conn.execute(
            CHECK_PASSWORD, login=login, password=password
        )
        user_id = await result.scalar()

    return make_login_response(user_id)


async def user_groups(request):
    user_id = request.match_info.get('id', None)

    async with request.app['db'].acquire() as conn:
        if await exist_user(user_id, conn) == None:
            return web.json_response({'error': 'user does not exist'}, status=404)
        groups = await get_user_groups(user_id, conn)

    return web.json_response({'groups': [row['group_name'] for row in groups]})


async def check_create_group_params(name, conn):
    if not type(name) is str:
        return 'group name not a string'
    if len(name) == 0:
        return 'group name is empty'
    if name.lower() != name:
        return 'group name not in lowercase'
    if await get_group_id_by_name(name, conn) != None:
        return 'group already exists'
    else:
        return None


async def create_group(request):
    params = await request.json()
    name = params.get('name', '')

    async with request.app['db'].acquire() as conn:
        error = await check_create_group_params(name, conn)
        if error:
            msg = {'error': error}
        else:
            await conn.execute(
                ADD_GROUP, name=name
            )
            msg = {'group_id': await get_group_id_by_name(name, conn)}

    return web.json_response(msg)


async def add_user_to_group(group_id, user_id, conn):
    user_in_group = await check_user_in_group(user_id, group_id, conn)
    if user_in_group == None:
        await conn.execute(
            ADD_USER_IN_GROUP, user_id=user_id, group_id=group_id
        )
    return {'msg': 'user {} added to group {}'.format(user_id, group_id)}


async def delete_user_from_group(group_id, user_id, conn):
    user_in_group = await check_user_in_group(user_id, group_id, conn)
    if user_in_group != None:
        await conn.execute(
            DEL_USER_FROM_GROUP, user_id=user_id, group_id=group_id
        )
        return {'msg': 'user {} deleted from group {}'.format(user_id, group_id)}
    else:
        return {'msg': 'user {} not in group {}'.format(user_id, group_id)}


async def check_manage_group_params(group_id, user_id, conn):
    if await exist_group(group_id, conn) == None:
        return 'group does not exist'
    user_id_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    if not type(user_id) is str or not re.match(user_id_pattern, user_id):
        return 'incorrect type of user ID'
    if await exist_user(user_id, conn) == None:
        return 'user does not exist'
    else:
        return None


async def manage_group(request):
    group_id = int(request.match_info.get('id', 0))
    params = await request.json()
    action = params.get('action', None)
    user_id = params.get('user_id', '')

    async with request.app['db'].acquire() as conn:
        error = await check_manage_group_params(group_id, user_id, conn)
        if error:
            msg = {'error': error}
        elif action == 'add_user':
            msg = await add_user_to_group(group_id, user_id, conn)
        elif action == 'del_user':
            msg = await delete_user_from_group(group_id, user_id, conn)
        else:
            msg = {'error': 'unknown type of operation'}

    return web.json_response(msg)


async def user_ws_handler(request):
    user_id = request.match_info.get('user_id')

    async with request.app['db'].acquire() as conn:
        if await exist_user(user_id, conn) == None:
            return web.json_response({'error': 'user does not exist'}, status=404)


    ws = web.WebSocketResponse()
    await ws.prepare(request)
    while True:
        await ws.send_json({'msg': 'message for user {}'.format(user_id)})
        await asyncio.sleep(2)


async def group_ws_handler(request):
    group = request.match_info.get('group')
    user_id = request.headers.get('Authentication', '')

    if not re.match(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', user_id):
        return web.json_response({'error': 'incorrect user id'})

    async with request.app['db'].acquire() as conn:
        group_id = await get_group_id_by_name(group, conn)
        if group_id == None:
            return web.json_response({'error': 'group does not exist'}, status=404)
        if await check_user_in_group(user_id, group_id, conn) == None:
            return web.json_response({'error': 'user not in group'})

    ws = web.WebSocketResponse()
    await ws.prepare(request)
    while True:
        await ws.send_json({'msg': 'message for members of group {}'.format(group)})
        await asyncio.sleep(2)

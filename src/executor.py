#!/usr/bin/env python
# coding: utf-8
# yc@2019/04/12
'''
Usage:
    ./executor.py <my_jid> <my_passwd> <master_jid>
When received a message from <master_jid>, say 'test fire',
will execute a bash script like this:
    bash cmds/test.sh fire
'''

import re
import time
import asyncio
import contextvars
from pathlib import Path
from datetime import timedelta

import fire
import aioxmpp
import aioxmpp.dispatcher

import utils


CMD_PATH = Path(__file__).resolve().parent.joinpath('cmds')

xmpp_client = contextvars.ContextVar('active xmpp client')
logger = utils.make_file_logger('executor')


def message_received(msg):
    if not msg.body:
        return
    if aioxmpp.MessageType.CHAT != msg.type_:
        return
    reply = msg.make_reply()
    text = msg.body.any().strip()
    if not text:
        return
    if text.startswith(('?OTR', 'I sent you an OMEMO encrypted message but')):
        body = 'I don\'t support OTR/OMEMO yet, send me plain text please!'
    # cmd
    args = text.split(' ')
    arg0 = args[0].lower()
    if not re.match(r'^[a-z0-9_.-]+$', arg0):
        return
    script = CMD_PATH.joinpath('{}.sh'.format(arg0))
    if not script.is_file():
        body = 'script {}.sh not exists'.format(arg0)
    else:
        cmd = ['bash', script] + args[1:]
        try:
            body = utils.shell(cmd).decode('utf-8').strip()
        except ValueError as e:
            body = 'ERR: {}'.format(e.args[0])
        except Exception as e:
            body = 'EXP: {}'.format(e)
    reply.body[None] = body
    xmpp_client.get().enqueue(reply)


async def _executor(my_jid, my_passwd, master_jid):
    master = aioxmpp.JID.fromstr(master_jid)
    client = aioxmpp.PresenceManagedClient(
        aioxmpp.JID.fromstr(my_jid),
        aioxmpp.make_security_layer(my_passwd),
    )
    # auto re-connect every 10s after conn down
    client.backoff_factor = 1
    client.backoff_cap = timedelta(seconds=10)
    xmpp_client.set(client)
    message_dispatcher = client.summon(
        aioxmpp.dispatcher.SimpleMessageDispatcher
    )
    message_dispatcher.register_callback(
        aioxmpp.MessageType.CHAT,
        master,
        message_received,
    )
    roster_client = client.summon(aioxmpp.RosterClient)
    while True:
        try:
            async with client.connected():
                roster_client.approve(master)
                roster_client.subscribe(master)
                logger.info('Connected')
                await asyncio.sleep(time.time())
        except asyncio.CancelledError:
            # asyncio.sleep
            # KeyboardInterrupt
            raise
        except Exception as e:
            logger.warning(repr(e))


def executor(my_jid, my_passwd, master_jid):
    asyncio.run(_executor(my_jid, my_passwd, master_jid))


if __name__ == '__main__':
    fire.Fire(executor)

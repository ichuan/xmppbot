#!/usr/bin/env python
# coding: utf-8
# yc@2019/04/12
'''
Usage:
    ./executor.py <my_jid> <my_passwd> <master_jid>
When received a message from <master_jid>, say 'test fire',
will execute a bash script like this:
    bash cmds/test.sh fire

<master_jid> can be comma-separated multi jids
'''

import re
import time
import asyncio
from pathlib import Path
from datetime import timedelta

import fire
import aioxmpp
import aioxmpp.dispatcher

import utils


CMD_PATH = Path(__file__).resolve().parent.joinpath('cmds')
# 3min
SUBPROCESS_MAX_RUNTIME = 3 * 60

G = {
    'client': None,
    'proc': None,
}
logger = utils.make_file_logger('executor')


async def _continuous_send_output(reply, stream):
    while not stream.at_eof():
        bytes_ = []
        while not stream.at_eof():
            try:
                byte = await asyncio.wait_for(stream.read(1), timeout=1)
                if byte:
                    bytes_.append(byte)
            except asyncio.TimeoutError:
                break
        if bytes_:
            reply.body[None] = b''.join(bytes_).decode('utf-8')
            await G['client'].send(reply)
    return b'Process done'


async def _message_received(msg):
    if not msg.body:
        return
    if aioxmpp.MessageType.CHAT != msg.type_:
        return
    reply = msg.make_reply()
    text = msg.body.any().strip()
    if not text:
        return
    # previous session?
    if G['proc'] and G['proc'].returncode is None:
        if text == 'KILL':
            G['proc'].kill()
        else:
            G['proc'].stdin.write(text.encode('utf-8') + b'\n')
            await G['proc'].stdin.drain()
        return
    if text.startswith(('?OTR', 'I sent you an OMEMO encrypted message but')):
        body = 'I don\'t support OTR/OMEMO yet, send me plain text please!'
    # cmd
    args = text.split(' ')
    arg0 = args[0].lower()
    if not re.match(r'^[^_][a-z0-9_.-]+$', arg0):
        return
    script = CMD_PATH.joinpath('{}.sh'.format(arg0))
    if not script.is_file():
        body = 'script {}.sh not exists'.format(arg0)
    else:
        cmd = ['bash', script.as_posix()] + args[1:]
        try:
            G['proc'] = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                # 64KB output max
                limit=65_536,
                bufsize=0,
                cwd=CMD_PATH,
            )
            await asyncio.wait_for(
                _continuous_send_output(reply, G['proc'].stdout),
                # G['proc'].communicate(),
                timeout=SUBPROCESS_MAX_RUNTIME,
            )
            return
        except asyncio.TimeoutError:
            body = 'cmd "{}" timed out and terminated'.format(cmd)
        except Exception as e:
            body = 'Exception: {}'.format(e)
        finally:
            if G['proc'] and G['proc'].returncode is None:
                G['proc'].terminate()
            G['proc'] = None
    reply.body[None] = body
    await G['client'].send(reply)


def message_received(msg):
    asyncio.create_task(_message_received(msg))


async def _executor(my_jid, my_passwd, master_jid):
    masters = [aioxmpp.JID.fromstr(i) for i in master_jid.split(',')]
    client = aioxmpp.PresenceManagedClient(
        aioxmpp.JID.fromstr(my_jid), aioxmpp.make_security_layer(my_passwd),
    )
    # auto re-connect every 10s after conn down
    client.backoff_factor = 1
    client.backoff_cap = timedelta(seconds=10)
    G['client'] = client
    message_dispatcher = client.summon(aioxmpp.dispatcher.SimpleMessageDispatcher)
    for m in masters:
        message_dispatcher.register_callback(
            aioxmpp.MessageType.CHAT, m, message_received,
        )
    roster_client = client.summon(aioxmpp.RosterClient)
    while True:
        try:
            async with client.connected():
                for m in masters:
                    roster_client.approve(m)
                    roster_client.subscribe(m)
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

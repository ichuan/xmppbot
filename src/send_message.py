#!/usr/bin/env python
# coding: utf-8
# yc@2019/04/12
'''
Usage:
    ./send_message.py <from_jid> <from_passwd> <to_jid> <message>
'''

import asyncio

import fire
import aioxmpp


async def _send_message(from_jid, from_passwd, to_jid, message):
    client = aioxmpp.PresenceManagedClient(
        aioxmpp.JID.fromstr(from_jid),
        aioxmpp.make_security_layer(from_passwd),
    )
    msg = aioxmpp.Message(
        to=aioxmpp.JID.fromstr(to_jid),
        type_=aioxmpp.MessageType.CHAT,
    )
    msg.body[None] = message
    async with client.connected():
        await client.send(msg)


def send_message(from_jid, from_passwd, to_jid, message):
    asyncio.run(_send_message(from_jid, from_passwd, to_jid, message))


if __name__ == '__main__':
    fire.Fire(send_message)

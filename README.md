# xmppbot
A python based xmppbot for dev-ops purpose (alerting and automation).

## Dependences
- Python3.7+

## `send_message.py`
Send a XMPP message to a JID. Useful for system alerting. Usage:

```
python src/send_message.py <from_jid> <from_passwd> <to_jid> <message>
```


## `executor.py`
Listening to messages from a JID (Master), and execute corresponding shell scripts. 
Useful for manage a server through XMPP. This will start a XMPP bot daemon:

```
python src/executor.py <my_jid> <my_passwd> <master_jid>
```

Where `<master_jid>` is the authed JID. Write your own scripts in `src/cmds`, 
when received a message `test fire` form JID, the following command will be executed:

```
bash /path/to/src/cmds/test.sh fire
```

And the stdout/stderr will be replied to JID.

## On cmds
- cmd with filename startwith `_` is excluded
- If you want a cmd to be confirmed before executing (i.e. dangerous cmd), `source _require_confirmation.sh` at file top

# quickstart-autobahn-python-component

Two WAMP clients using either Twisted or asyncio.

Each script takes some options to specify how to connect to the
router, the realm to use, etc. Run either one to see the options:

   python client_tx.py --help
   python client_aio.py --help

You can run more than one client at once to see what happens with
publishes, etc.

There is also a second style of using the Component API demonstrated
by passing a "main=" function. Also, instead of using decorators,
methods are registered (or subscribed) using calls to the session
object. This might make more sense if the WAMP URIs are dynamic (for
example) or to invert the program flow.

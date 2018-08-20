import os
import argparse
import six
import txaio

from asyncio import sleep
from autobahn.wamp.types import RegisterOptions
from autobahn.wamp.exception import ApplicationError
from autobahn.asyncio.component import Component, run


def create_component(args, extra):

    log = txaio.make_logger()

    # 'transports' can also be a list of dicts containing more
    # detailed connection information (and multiple ways to connect)
    client = Component(
        transports=args.url,
        realm=args.realm,
        extra=extra,
        authentication={
            "anonymous": {
                "authrole": "anonymous",
            },
        }
    )

    info = {
        "ident": "unknown",
        "type": "Python",
    }

    @client.on_connect
    def connected(session, x):
        log.info("Client connected: {klass}, {extra}", klass=session.__class__, extra=session.config.extra)

    @client.on_join
    async def joined(session, details):
        log.info("Joined: {details}", details=details)

        info["ident"] = details.authid

        log.info("Component ID is  {ident}", **info)
        log.info("Component type is  {type}", **info)

        # this could go in a "main" procedure to be passed to
        # Component, declared as "def main(reactor, session):" and
        # passed to Component() via "main="
        x = 0
        counter = 0
        while True:

            # CALL
            try:
                res = await session.call(u'com.example.add2', x, 3)
                print('----------------------------')
                log.info("add2 result: {result}", result=res[0])
                log.info("from component {id} ({type})", id=res[1], type=res[2])
                x += 1
            except ApplicationError as e:
                # ignore errors due to the frontend not yet having
                # registered the procedure we would like to call
                if e.error != 'wamp.error.no_such_procedure':
                    raise e

            # PUBLISH
            # (we only have to 'await' publish() if we asked for an acknowledge)
            session.publish(u'com.example.oncounter', counter, info["ident"], info["type"])
            print('----------------------------')
            log.info("published to 'oncounter' with counter {counter}",
                     counter=counter)
            counter += 1

            await sleep(2)  # note this is an "async sleep" using callLater()

    @client.register(
        "com.example.add2",
        options=RegisterOptions(invoke=u'roundrobin'),
    )
    def add2(a, b):
        print('----------------------------')
        print("add2 called on {}".format(info["ident"]))
        return [ a + b, info["ident"], info["type"]]


    @client.subscribe("com.example.oncounter")
    def oncounter(counter, ident, kind):
        print('----------------------------')
        log.info("'oncounter' event, counter value: {counter}", counter=counter)
        log.info("from component {ident} ({kind})", ident=ident, kind=kind)

    @client.on_leave
    def left(session, details):
        log.info("session left: {}".format(details))

    return client


if __name__ == '__main__':

    # Crossbar.io connection configuration
    url = os.environ.get('CBURL', u'ws://localhost:8080/ws')
    realm = os.environ.get('CBREALM', u'realm1')

    # parse command line parameters
    parser = argparse.ArgumentParser()

    parser.add_argument('-d',
                        '--debug',
                        action='store_true',
                        help='Enable debug output.')

    parser.add_argument('--url',
                        dest='url',
                        type=six.text_type,
                        default=url,
                        help='The router URL (default: "ws://localhost:8080/ws").')

    parser.add_argument('--realm',
                        dest='realm',
                        type=six.text_type,
                        default=realm,
                        help='The realm to join (default: "realm1").')

    parser.add_argument('--service_name',
                        dest='service_name',
                        type=six.text_type,
                        default=None,
                        help='Optional service name.')

    parser.add_argument('--service_uuid',
                        dest='service_uuid',
                        type=six.text_type,
                        default=None,
                        help='Optional service UUID.')

    args = parser.parse_args()

    log_level = 'debug' if args.debug else 'info'

    # any extra info we want to forward to our ClientSession (in self.config.extra)
    extra = {
        u'service_name': args.service_name,
        u'service_uuid': args.service_uuid,
    }
    component = create_component(args, extra)

    # starts the reactor, and logging -- this won't return unless all
    # our components complete
    run([component])

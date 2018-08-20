import os
import argparse
import six
import txaio

from asyncio import sleep
from autobahn.wamp.types import RegisterOptions
from autobahn.wamp.exception import ApplicationError
from autobahn.asyncio.component import Component, run


async def main(reactor, session):

    log = txaio.make_logger()
    info = session.config.extra

    def add2(a, b):
        print('----------------------------')
        print("add2 called on {}".format(info["service_name"]))
        return [ a + b, info["service_name"] ]
    await session.register(
        add2,
        "com.example.add2",
        options=RegisterOptions(invoke=u'roundrobin'),
    )

    def oncounter(counter, ident, kind):
        print('----------------------------')
        log.info("'oncounter' event, counter value: {counter}", counter=counter)
        log.info("from component {ident} ({kind})", ident=ident, kind=kind)
    await session.subscribe(oncounter, "com.example.oncounter")

    x = 0
    counter = 0
    while True:

        # CALL
        try:
            res = await session.call(u'com.example.add2', x, 3)
            print('----------------------------')
            log.info("add2 result: {result}", result=res[0])
            log.info("from component {id}", id=res[1])
            x += 1
        except ApplicationError as e:
            # ignore errors due to the frontend not yet having
            # registered the procedure we would like to call
            if e.error != 'wamp.error.no_such_procedure':
                raise e

        # PUBLISH
        session.publish(u'com.example.oncounter', counter, info["service_name"])
        print('----------------------------')
        log.info("published to 'oncounter' with counter {counter}",
                 counter=counter)
        counter += 1

        await sleep(2)  # note this is an "async sleep" using callLater()


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
        u'service_name': args.service_name or "default",
        u'service_uuid': args.service_uuid,
    }
    client = Component(
        transports=args.url,
        realm=args.realm,
        main=main,
        extra=extra,
        authentication={
            "anonymous": {
                "authrole": "anonymous",
            },
        }
    )

    # starts the reactor, and logging -- this won't return unless all
    # our components complete
    run([client])

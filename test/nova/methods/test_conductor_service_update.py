__author__ = 'jonathan'

import test.nova._fixtures as models
from lib.rome.core.orm.query import Query

from lib.rome.core.orm.query import Query as RomeQuery
from lib.rome.core.session.session import Session as RomeSession

from test.nova.methods.test_ensure_default_secgroup import _security_group_ensure_default, _security_group_get_query

import logging
import uuid

from oslo.serialization import jsonutils

LOG = logging.getLogger()

# List of fields that can be joined in DB layer.
_INSTANCE_OPTIONAL_JOINED_FIELDS = ['metadata', 'system_metadata',
                                    'info_cache', 'security_groups',
                                    'pci_devices']
# These are fields that are optional but don't translate to db columns
_INSTANCE_OPTIONAL_NON_COLUMN_FIELDS = ['fault', 'numa_topology',
                                        'pci_requests']

# These are fields that can be specified as expected_attrs
INSTANCE_OPTIONAL_ATTRS = (_INSTANCE_OPTIONAL_JOINED_FIELDS +
                           _INSTANCE_OPTIONAL_NON_COLUMN_FIELDS)

def get_session(use_slave=False, **kwargs):
    # return FakeSession()
    return RomeSession()
    # return OldRomeSession()


def model_query(context, *args, **kwargs):
    # base_model = kwargs["base_model"]
    # models = args
    return RomeQuery(*args, **kwargs)

def _service_get(context, service_id, with_compute_node=True, session=None,
                 use_slave=False):
    query = model_query(context, models.Service, session=session,
                        use_slave=use_slave).\
                     filter_by(id=service_id)

    # if with_compute_node:
    #     query = query.options(joinedload('compute_node'))

    result = query.first()
    if not result:
        raise Exception()

    return result

def db_service_update(context, service_id, values):
    session = get_session()
    with session.begin():
        service_ref = _service_get(context, service_id,
                                   with_compute_node=False, session=session)
        if values.keys() == ["report_count"]:
            if not values["report_count"] == service_ref.report_count:
                service_ref.update(values)
                # TODO (Jonathan): add a "session.add" to ease the session management :)
                session.add(service_ref)

    return service_ref

def conductor_service_update(context, service, values):
        svc = db_service_update(context, service['id'], values)
        return jsonutils.to_primitive(svc)

class Context(object):
    def __init__(self, project_id, user_id):
        self.project_id = project_id
        self.user_id = user_id

class ModelInstance(dict):
    def __init__(self):
        self.fields = []
        self.deleted = None
        self.cleaned = None

def test_service_update():
    context = Context("project1", "user1")

    # session = get_session()
    # Create a service
    service = models.Service()
    service.host = "host1"
    service.binary = "binary1"
    service.topic = "topic1"
    service.report_count = 0
    service.save()
    # session.add(service)

    compute_nodes = []
    for i in range(0, 2):
        compute_node = models.ComputeNode()
        compute_node.vcpus = 12
        compute_node.service = service

        compute_node.save()
        compute_nodes += [compute_node]
        # session.add(compute_node)

    service_ref = conductor_service_update(context, service, {"report_count": 1})
    print(type(service_ref))

    print(service_ref)

    assert type(service_ref) == dict

if __name__ == '__main__':

    logging.getLogger().setLevel(logging.DEBUG)

    context = Context("project1", "user1")

    test_service_update()

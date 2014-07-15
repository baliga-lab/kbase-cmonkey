import WorkspaceClient as wsc
import CmonkeyClient as cmc
import UserAndJobStateClient as ujs

"""
KBase is a distributed platform which provides a REST API to its services.

This is an attempt to provide a Python friendly API to KBase for use with
with cmonkey and Inferelator.

It converts cmonkey standard datatypes to KBase datatypes and abstracts
calls.
"""
WORKSPACE_URL = 'https://kbase.us/services/ws'
CM_URL = 'http://140.221.85.173:7078'
UJS_URL = 'https://kbase.us/services/userandjobstate'

class WorkspaceInstance(object):
    """representation of a KBase workspace instance"""

    def __init__(self, ws_service, ws_meta):
        self.ws_service = ws_service
        self.ws_meta = ws_meta

    def id(self):
        return self.ws_meta[6]

    def name(self):
        return self.ws_meta[0]

    def __repr__(self):
        return "{Workspace, name: %s, id: %d}" % (self.name(), self.id())

    def save_object(self, objtype, objid, data):
        """Generic way to store an object into KBase, class-specific save functions
        call this one"""
        return self.ws_service.save_object({'workspace': self.name(),
                                            'type': objtype,
                                            'id': objid,
                                            'data': data})


class WorkspaceObject(object):
    """an object that is stored in a workspace"""

    def __init__(self, ws_inst, id, version=1):
        self.ws = ws_inst
        self.id = id
        self.version = version

    def obj_ref(self):
        """Build an object reference"""
        return "%s/%s/%s" % (self.ws.id(), self.id, self.version)


def __workspaces(ws_service, exclude_global=True):
  no_global = 1 if exclude_global else 0
  for meta in ws_service.list_workspaces({'excludeGlobal': no_global}):
      yield WorkspaceInstance(ws_service, meta)

def workspaces_for(user, password, service_url=WORKSPACE_URL):
    ws_service = wsc.Workspace(service_url, user_id=user, password=password)
    return [ws for ws in __workspaces(ws_service)]

def workspace(user, password, name, search_global=False, service_url=WORKSPACE_URL):
    ws_service = wsc.Workspace(service_url, user_id=user, password=password)
    for ws in __workspaces(ws_service, not search_global):
        print "comparing with %s" % ws.name()
        if ws.name() == name:
            return ws
    raise Exception("no workspace named '%s' found !" % name)



"""
Gene Expressions
"""

def save_expression_sample(ws, id, condition, gene_pvals, genome_id):
  """
  condition -> source_id"""
  data = {'id': id,
          'source_id': condition,
          'type': 'microarray',
          'numerical_interpretation': 'undefined',
          'external_source_date': 'unknown',
          'expression_levels': gene_pvals,
          'genome_id': genome_id}

  return ws.save_object('KBaseExpression.ExpressionSample-1.2', id, data)

def save_expression_series(ws, name, source_file,
                           genome_id, sample_ids):
  """
  Gene expressions in KBase are stored as a list of ExpressionSeries
  Parameters:
  - ws: Workspace service interface
  - workspace: workspace object
  - name: unique name the object should be stored under
  - source_file: source file
  - genome_id: the unique name of the genome this expression series is based on
  - sample_ids: a list of ExpressionSample ids, in KBase standard identifier format
  """
  data = {'id': name, 'source_id': source_file,
          'external_source_date': 'unknown',
          'genome_expression_sample_ids_map': {genome_id: sample_ids}}
  return ws.save_object('KBaseExpression.ExpressionSeries-1.0', name, data)

"""
Interaction Sets
"""
def save_interaction_set(ws, name, nwtype, edges):
    """Save an interaction set, this is for things like STRING networks and operons
    """
    def dataset_source(id, desc, url):
        return {'id': id, 'name': id,
                'reference': 'N/A',
                'description': desc,
                'resource_url': url}

    def interaction(id, node1, node2, nwtype, score_name, weight):
        return {'id': id, 'type': nwtype,
                'entity1_id': node1, 'entity2_id': node2,
                'scores': {score_name: weight} }

    interactions = []
    for i, edge in enumerate(edges):
        n1, n2, weight = edge
        interactions.append(interaction('edge-%d' % i, n1, n2, nwtype, 'pval', weight))

    data = {'id': name, 'name': name,
            'description': 'my network',
            'type': 'somenetwork',
            'source': dataset_source('%s-source' % name, 'some description', ''),
            'interactions': interactions}

    return ws.save_object('KBaseNetworks.InteractionSet-1.0', name, data)

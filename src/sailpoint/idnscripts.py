import logging
from rich.pretty import pretty_repr as pretty

log = logging.getLogger(__name__)


class SODChecker:
    """
    Checks SOD violations and resolves violations by removing violating
    access items
    """

    def __init__(self, idn, report_only=True):
        self.report_only = report_only
        self.reason = (
            'Automatically removing access due to violation  of Separation '
            'of Duties SoD rule'
        )
        self.idn = idn

    def remove_access(self, violator, access, reason):
        '''removes the access from the violator

        Removes access from an SOD violator

        Parameters
        --------------------
        violator: The violator ID


        sort: string
            The key to sort on. Default is 'id'

        Results
        --------------------
        True if access was removed
        False if not

        '''
        if self.report_only:
            log.warning(
                f'Report Only: Remove {access.get("name")} from '
                f'{violator.get("name")} - ACCESS NOT REMOVED'
            )
            return False

        payload = {
            "requestedFor": [violator.get('id')],
            "requestType": "REVOKE_ACCESS",
            "requestedItems": [
                {
                    "type": access.get('type'),
                    "id": access.get('id'),
                    "comment": reason,
                }
            ],
        }
        log.debug(pretty(payload))
        endpoint = 'access-requests'
        ret = self.idn.api(
            endpoint=endpoint, api='beta', payload=payload, method='POST'
        )
        log.debug(pretty(ret))
        log.debug(pretty(ret.text))
        if ret.status_code == 202:
            return True
        ret = ret.json()
        if ret.get('detailCode') == '400.1 Bad request content':
            # This happens when we are trying to remove a violation item from a
            # user but they don't have it which may be true for a lot of the
            # violating items
            cause = ret.get('causes', [])[0]
            cause_text = cause.get('text')

            if 'Some items are not revocable' in cause_text:
                log.debug(cause.get('text'))
                # log.info(pretty(ret))
                return False
            else:
                log.error(pretty(access))
                log.error(pretty(payload))
                log.error(pretty(ret))
                log.error(pretty(cause))
                raise Exception(cause_text)

        return True

    def fix_violation(self, sod_policy, violator):
        # log.info(pretty(sod_policy.get('conflictingAccessCriteria')))
        for c, criteria in sod_policy.get('conflictingAccessCriteria').items():
            criteria_name = criteria.get('name')
            if criteria_name == 'Restricted Access':
                # remove this access
                for access in criteria.get('criteriaList', []):
                    # remove
                    log.debug('Removing:')
                    log.debug(pretty(access))
                    if self.remove_access(violator, access, self.reason):
                        log.info(
                            f'Removed Access: {access.get("name")} from '
                            f'{violator.get("name")}'
                        )
                        log.debug(pretty(access))

    def get_violators(self, sod_policy):
        '''Gets the violators of a spcified sod_policy

        Parameters
        -------------------
        sod_policy: dict - the SOD policy to find violations for

        '''
        pol_query = sod_policy.get('policyQuery')
        payload = {"query": {"query": pol_query}, "indices": ["identities"]}
        violators = []
        for r in self.idn.search(payload, sort='id'):
            violators.append(r)
        return violators

    def process_sod(self, sod):
        '''Processes the SOD to remove violations

        Processes a SOD and find violators and remove their violating access

        Parameters
        --------------------
        sod: The SOD to process

        Results
        --------------------
        returns None
        '''
        # log.debug(sod)

        sod_id = sod.get('objectRef', {}).get('id')
        endpoint = f'sod-policies/{sod_id}'
        sod_policy = self.idn.api(endpoint=endpoint, api='beta').json()
        sod_name = sod_policy.get('name')
        log.info(f'Processing SOD: {sod_name} - {sod_id}')
        log.debug(pretty(sod_policy))
        violators = self.get_violators(sod_policy)
        log.info(f'Number of violators: {len(violators)}')
        for v in violators:
            log.warning(
                f'Found Violator: {v.get("name")} '
                f'on SOD: {sod_policy.get("name")}'
            )
            self.fix_violation(sod_policy, v)

    def process(self):
        # Search all SOD Policies
        for sod in self.idn.api(
            endpoint='tagged-objects/SOD_POLICY', api='beta'
        ).json():
            # Get the tags and find ones with NO_EXCEPTIONS
            tags = sod.get('tags', [])
            if 'NO_EXCEPTIONS' in tags:
                # found a SOD to process
                log.info('found a SOD to process')
                self.process_sod(sod)

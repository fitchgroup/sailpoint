import logging
from rich.pretty import pretty_repr

log = logging.getLogger(__name__)


class IDNReport:
    def __init__(self, api, idn):
        self.api = api
        self.idn = idn  # the idn util object

    def get_disabled_gg_members(self):
        disabled_gg_members = []
        # Find all governance groups
        ret = self.idn.api('workgroups', api='v2')
        for gg in ret.json():
            ggid = gg.get('id', None)
            if ggid:
                # Get the members
                gg_mbrs = self.idn.get_gg_members(ggid)
                for m in gg_mbrs:
                    # Get the identity for each member
                    log.debug(m)
                    user = self.idn.get_user_by_id(m.get('externalId', None))
                    # log.debug(user)
                    status = user.get('status', None)
                    if status != 'ACTIVE':
                        attrs = user.get('attributes', {})
                        record = {
                            'Governance Group': gg.get('name', None),
                            'Member Name': user.get('name', None),
                            'Status': user.get('status', None),
                            'LifeCycle': attrs.get(
                                'cloudLifecycleState', None
                            ),
                        }

                        disabled_gg_members.append(record)
        return disabled_gg_members

    def get_disabled_ap_owners(self):
        # It would be much faster to get the list of disabled AP owners using
        # search: owns.accessProfiles.id:* AND
        # attributes.cloudLifecycleState:terminated Then query APs with those
        # owners payload:

        payload = {
            "query": {
                "query": "owns.accessProfiles.id:* AND NOT attributes.cloudLifecycleState:active"
            },
            "indices": ["identities"],
            "includeNested": False,
            "sort": ["displayName"],
        }

        disabled_owners = self.idn.search(payload=payload)

        disabled_ap_owners = []
        for owner in disabled_owners:
            owner_id = owner.get('id')

            # Get Access Profiles for disabled owner
            ret = self.api(
                f'access-profiles?filters=owner.id eq "{owner_id}"', api='beta'
            )
            log.info(ret)
            log.info(ret.text)
            log.info(ret.json())
            for ap in ret.json():
                apid = ap.get('id', None)
                if apid:
                    ap_name = ap.get('name', None)
                    user_name = owner.get('name', None)
                    user_status = owner.get('status', None)
                    attrs = owner.get('attributes', {})
                    user_lifecycle = attrs.get('cloudLifecycleState', None)
                    log.debug(f'Found disabled user: {user_name}')
                    record = {
                        'Access Profile': ap_name,
                        'Owner Name': user_name,
                        'Status': user_status,
                        'LifeCycle': user_lifecycle,
                    }

                    disabled_ap_owners.append(record)
        return disabled_ap_owners

    def get_ai_recommendations(self, id):
        '''
        Get access recommendations for an identity

        Parameters
        --------------------
        id: string
            The ID of the user you want to get recommendations for


        '''

        ret = self.api(
            f'access-request-recommendations/?identity-id={id}', api='beta'
        )
        log.info(ret)
        log.info(ret.text)
        log.info(ret.json())


if __name__ == '__main__':
    pass

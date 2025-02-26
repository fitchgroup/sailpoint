import logging
from rich.pretty import pretty_repr

log = logging.getLogger(__name__)


class IDNReport:
    """
    Standard reports from IDN
    """

    def __init__(self, api, idn):
        self.api = api
        self.idn = idn  # the idn util object
        self.user_cache = {}  # User cache index for get_user_by_id_cache fn

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
                    user = self.idn.get_user_by_id(m.get('id', None))
                    # log.debug(user)
                    attrs = user.get('attributes', {})
                    status = attrs.get('cloudLifecycleState', None)
                    if status != 'active':
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

    # Build cache so we don't look up users multiple times
    def get_user_by_id_cache(self, user_id):
        '''
        Gets a user by their ID, but also caches results so next time the
        lookup doesn't have to go to the API
        '''
        if user_id in self.user_cache:
            return self.user_cache[user_id]
        else:
            user = self.idn.get_user_by_id(user_id)
            self.user_cache[user_id] = user
            return user

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
            log.debug(ret)
            log.debug(ret.text)
            log.debug(ret.json())
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

    def gg_membership(self):
        '''
        Outputs a list of Governance groups, members and the associations one per line
        '''
        log.warning('This function takes a while to run')
        gg_members = {}
        # Retrieve all Governance Groups with their members and connections
        gg_list = self.idn.get_gg(members=True, connections=True)
        count = 0

        # Iterate over each Governance Group
        for gg in gg_list:
            count += 1
            log.debug(count)
            log.debug(gg.get('name'))
            gg_members_list = gg.get('members', [])

            # Iterate over all members in the current Governance Group
            for member in gg_members_list:
                # Log the member information
                # log.info(member)
                # Retrieve details for each member
                user = self.get_user_by_id_cache(member.get('id'))
                attributes = user.get('attributes', {})

                # Iterate over all connections for the Governance Group
                for connection in gg.get('connections', []):
                    # Construct the record for the current member
                    record = {
                        'Governance Group': gg.get('name'),
                        'Member Name': user.get('name'),
                        'Identity ID': user.get('id'),
                        'LifeCycle': attributes.get('cloudLifecycleState'),
                        'Employee Number': user.get('employeeNumber'),
                        'AD Username': attributes.get('username'),
                        'Item Type': connection.get('object', {}).get(
                            'type', ''
                        ),
                        'Item Name': connection.get('object', {}).get(
                            'name', ''
                        ),
                        'Item Description': connection.get('object', {}).get(
                            'description', ''
                        ),
                        'Item ID': connection.get('object', {}).get('id', ''),
                    }
                    log.debug(pretty_repr(record))
                    if not user.get('id') in gg_members:
                        gg_members[user.get('id')] = []
                    gg_members[user.get('id')].append(record)
                    # log.info(pretty(gg_members))

        return gg_members

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
        log.debug(ret)
        log.debug(ret.text)
        log.debug(ret.json())


if __name__ == '__main__':
    pass

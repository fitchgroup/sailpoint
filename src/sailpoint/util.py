from .api import IDNApi
import io
import logging
import csv
import json

# from rich.str import str_repr as str
from rich.pretty import pretty_repr

log = logging.getLogger(__name__)


class IDN:
    def __init__(self, secret=None, client_id=None, tenant=None):
        idn_api = IDNApi(secret, client_id, tenant)
        self.api = idn_api.r
        pass

    def create_gg(self, name, description, owner_id):
        """Creates a Governance Group

        Parameters
        --------------------
        name: string
            The name of the Governance Group

        description: string
            The description for the Governance Group

        owner_id: string
            The Owner of the Access Profile specified by their loginID
            (sAMAccountName)


        Returns
        --------------------
        True

        """

        owner_idn = self.get_id_by_login(owner_id)[0]

        payload = {
            "name": name,
            "description": description,
            "owner": {"id": owner_idn.get('id')},
        }
        log.info('Creating Governance Group')
        log.debug(payload)
        ret = self.api('workgroups', api='v2', method='POST', payload=payload)
        log.debug(ret)
        log.debug(ret.text)
        log.debug(ret.json())
        return True

    def get_cc_id_for_id(self, idn_id):
        """
        Gets the 'cc' user ID for the ID that is passed in

        This is used, for example, when specifying an App Owner on an app. The
        API call for updating the app parameters is a CC API call, which requires
        you to use the 'cc' user ID.

        Parameters
        --------------------
        idn_id: dict
            The ID of the user you want to look up

        Returns
        --------------------
        cc_id: string - the users CC id if found

        """
        display_name = idn_id.get('displayName')
        external_id = idn_id.get('id')

        if not display_name:
            return

        filters = [
            {
                "joinOperator": "OR",
                "filter": [
                    {
                        "property": "displayName",
                        "operation": "STARTSWITH",
                        "value": display_name,
                    }
                ],
            }
        ]

        filter_str = json.dumps(filters)
        ret = self.api(f'user/list?filters={filter_str}', api='cc')
        log.debug(f'Looking for id: {external_id}')
        for i in ret.json()['items']:
            if i.get('externalId', None) == external_id:
                log.debug('found')
                log.debug(i)
                return i.get('id')

    def get_gg_members(self, ggid):
        """Get Governance Group members

        Parameters
        --------------------
        ggid: string
            The ID of the governance group that you want to get the members
            of

        Returns
        --------------------
        members: dict

        """
        # get governance group members
        ret = self.api(f'workgroups/{ggid}/members', api='v2')
        # print(ret)
        try:
            log.debug(pretty_repr(ret.json()))
            return ret.json()
        except:
            log.error(ret.status_code)
            log.error(ret.text)
            return None

    def get_org(self):
        """Gets the org information

        Returns
        --------------------
        org

        """

        log.debug('Getting tenant info')

        ret = self.api('org', api='v2')
        org = ret.json()

        #    for e in orgs:
        #        log.info(e)
        log.debug(str(org))
        return org

    def list_identity_attributes_source(self):
        """List all identity attributes from profile source"""
        ret = self.api('identity-profiles', method='GET', api='beta')
        attributes = ret.json()
        log.debug(str(attributes))
        return attributes

    def list_identity_attributes(self):
        """List all identity attributes"""
        ret = self.api('identityAttribute/list', method='GET', api='cc')
        attributes = ret.json()
        log.debug(str(attributes))
        return attributes

    def get_attribute_map(self, map_source):
        """Gets the attribute map"""
        target_attrs = self.list_identity_attributes()
        source_systems = self.list_identity_attributes_source()

        # reindex to attribute name
        attr_map = {}
        for s in source_systems:
            if s.get('name') == map_source:
                source_config = s.get('identityAttributeConfig')
                source_attrs = source_config.get('attributeTransforms')
        if source_attrs:
            log.debug('Got Source attributes')
            for a in source_attrs:
                attr_name = a.get('identityAttributeName')
                attr_map[attr_name] = {'source': a, 'dest': []}
        log.debug(pretty_repr(target_attrs))
        for t in target_attrs:
            attr_name = t.get('name')
            targets = t.get('targets')
            if len(targets) > 0:
                attr_map[attr_name]['dest'] = targets

        return attr_map

    def get_entitlement_by_id(self, entitlement_id):
        """Gets an entitlement by its ID

        Parameters
        --------------------
        entitlement: string
            The ID that you want

        Returns
        --------------------
        entitlement: dict
            The entitlement

        """

        log.debug(f'Getting Entitlement with id: {entitlement_id}')

        ret = self.api(f'entitlements/{entitlement_id}', api='beta')
        entitlement = ret.json()

        #    for e in entitlements:
        #        log.info(e)
        log.debug(str(entitlement))
        return entitlement

    def get_entitlements_for_source(
        self, source_id, search_item='name', search_name=None
    ):
        """Gets entitlements for source

        Parameters
        --------------------
        source_id: string
            The source ID that you want the entitlements for.

        search_name: string (optional)
            The entitlement you want to search for.  In this case the 'name'
            represents the Entitlement Name as defined in the source schema.

        search_item: string (optional default is 'name')
            Either 'name' or 'id' so you can search on the name or on the
            ID of the entitlement.  In this case the 'id' represents the
            Entitlement ID as defined in the source schema.

        Returns
        --------------------
        entitlements: generator of dicts
            The entitlements

        """

        log.debug(f'Getting Entitlements for source: {source_id}')
        # parameters = f'filters=source.id in ("{source_id}")'
        parameters = f'filters=source.id eq "{source_id}"'

        if search_name:
            parameters = f'{parameters} and {search_item} eq "{search_name}"'

        offset = 0

        while True:
            ret = self.api(
                f'entitlements?offset={offset}&limit=250&sorters=id&{parameters}',
                api='beta',
            )
            log.debug(ret)
            log.debug(ret.text)
            log.debug(ret.status_code)
            if ret.status_code == 200:
                entitlements = ret.json()

                if len(entitlements) == 0:
                    break

                for e in entitlements:
                    offset += 1
                    yield (e)
            else:
                log.warning(ret.text)
                log.warning(ret.status_code)
                log.warning('Did not get 200 status_code - retrying')

    def get_id_by_login(self, login):
        """Gets an Identity for the login specified

        Parameters
        --------------------
        login: string
            The login for the identity you want to retrieve

        Returns
        --------------------
        ids: list
            The Identity

        """
        log.info('Getting id by login')
        payload = {
            "query": {
                "query": f"attributes.activeDirectoryUsername:\"{login}\""
            },
            "indices": ["identities"],
            "includeNested": "False",
            "sort": ["displayName"],
        }
        log.debug(payload)
        ret = self.api('search', method='POST', payload=payload)
        ids = ret.json()
        log.debug(ids)
        return ids

    def create_ap(
        self,
        name,
        description,
        source_name,
        owner_login=None,
        owner_email=None,
        enabled=True,
        entitlements=[],
    ):
        """Creates an Access Profile

        Parameters
        --------------------
        name: string
            The name of the Access Profile

        description: string
            The description for the Access Profile

        owner_login: string
            The Owner of the Access Profile specified by their loginID
            (sAMAccountName)

        owner_email: string
            The Owner of the Access Profile specified by their email
            if owner_login is specified, this will be given preference

        source_name: string
            The source of the Access Profile specified by its name

        enabled: boolean
            If the Access Profile is enabled or not

        entitlements: list of entitlement dicts (id, name, type)
            The list of entitlements that are included in this Access Profile

        Returns
        --------------------
        return: json - output from the api call

        """

        if owner_login:
            owner_idn = self.get_id_by_login(owner_login)[0]
        else:
            owner_idn = self.get_user_by_email(owner_email)[0]

        source_id = self.get_sourceid_for_name(source_name)

        payload = {
            "name": name,
            "description": description,
            "enabled": True,
            "owner": {
                "type": "IDENTITY",
                "id": owner_idn.get('id', None),
                "name": owner_idn.get('name', None),
            },
            "source": {"id": source_id, "type": "SOURCE", "name": source_name},
            "entitlements": entitlements,
            "requestable": True,
            "accessRequestConfig": {
                "commentsRequired": True,
                "denialCommentsRequired": False,
                "approvalSchemes": [
                    {
                        "approverType": "MANAGER",
                    }
                ],
            },
        }
        log.info('Creating Access Profile')
        log.debug(pretty_repr(payload))
        log.debug(json.dumps(payload))
        ret = self.api('access-profiles', method='POST', payload=payload)
        try:
            log.debug(pretty_repr(ret.json()))
            return ret.json()
        except:
            log.error(ret.status_code)
            log.error(ret.text)
            return none

    def get_aps_for_source(self, source_id=None, source_name=None):
        """Get access profiles for a specific source

        Parameters
        --------------------
        source_id: string
            The ID of the source

        source_name: string
            The Name of the source

        Either the name or the ID must be specified

        Returns
        --------------------
        access_profiles: generator of dicts
            The access profiles

        """

        if not source_id:
            source_id = self.get_sourceid_for_name(source_name)

        log.debug(f'Getting Entitlements for source: {source_id}')
        # parameters = f'filters=source.id in ("{source_id}")'
        parameters = f'filters=source.id eq "{source_id}"'

        offset = 0

        while True:
            ret = self.api(
                f'access-profiles?offset={offset}&limit=250&sorters=id&{parameters}',
                api='beta',
            )
            log.debug(ret)
            log.debug(ret.text)
            log.debug(ret.status_code)
            if ret.status_code == 200:
                access_profiles = ret.json()

                if len(access_profiles) == 0:
                    break

                for ap in access_profiles:
                    offset += 1
                    yield (ap)
            else:
                log.warning(ret.text)
                log.warning(ret.status_code)
                log.warning('Did not get 200 status_code - retrying')

    def update_entitlement(self, entitlement_id, attr='description', val=''):
        """Used to update the entitlement.

            Use case is to update the description.

            If you set this to blank it will get updated based on the source
            description at the time the next entitlement aggregation is run

        Parameters
        --------------------
        entitlement_id: string
            The entitlement that you want to update specified by its ID

        attr: string  (DEFAULT: description)
            The attribute you want to update.

        val: string (DEFAULT: EMPTY)
            The value that you want to save

        Returns
        --------------------
        entitlement: dict
            The entitlement as it is after it has been updated


        """
        ret = self.api(f'entitlements/{entitlement_id}', api='beta')
        log.debug('Before Update')
        log.debug(ret.json())
        #    # Bulk update not working
        #    # Bad Content Error
        #    # The request was syntactically correct but its content
        #    # is semantically invalid.
        #    payload = {
        #        "entitlementIds": [f"{entitlement_id}"],
        #        "jsonPatch": [
        #            {
        #                "op": "replace",
        #                "path": "description",
        #                "value": "My Test",
        #            }
        #        ],
        #    }
        #    log.info(payload)
        #    ret = self.api(
        #        'entitlements/bulk-update', payload=payload,
        #         method='POST', api='beta'
        #    )
        #
        #    log.info('Result of bulk update')
        #    log.info(ret.json())

        #    # The following PATCH method on dscription results in
        #    # 'Illegal attempt to modify "description" field.'
        #    new_header = {'Content-Type': 'application/json-patch+json'}
        #    payload = [
        #        {
        #            "op": "replace",
        #            # "path": "/attributes/description",
        #            "path": "/description",
        #            "value": "My Test Update",
        #        }
        #    ]
        #    log.info(payload)
        #    ret = self.api(
        #        f'entitlements/{entitlement_id}',
        #        payload=payload,
        #        headers=new_header,
        #        method='PATCH',
        #        api='beta',
        #    )
        #
        #    log.info('Result of PATCH update')
        #    log.info(ret.json())

        # first get it in its existing state
        entitlement = ret.json()
        source_id = entitlement.get('source', {}).get('id')
        log.debug(f'{source_id}')

        # override what we got
        entitlement[attr] = val

        # API requires you upload a CSV file with the values similar to how you
        # do in the UI

        # No need to write it to disk
        output = io.StringIO()
        cols = [
            'attributeName',
            'attributeValue',
            'displayName',
            'description',
            'privileged',
            'schema',
        ]
        writer = csv.writer(output, delimiter=',')
        writer.writerow(cols)
        writer.writerow(
            [
                entitlement.get('attribute', ''),
                entitlement.get('value', ''),
                entitlement.get('name', ''),
                entitlement.get('description', ''),
                str(entitlement.get('privileged', 'FALSE')).upper(),
                entitlement.get('sourceSchemaObjectType', 'group'),
            ]
        )
        # files = {'csvFile': open('test-entitlements.csv', 'rb')}
        log.debug(output)
        log.debug(output.getvalue())
        files = {'csvFile': io.StringIO(output.getvalue())}

        ret = self.api(
            f'entitlements/sources/{source_id}/entitlements/import',
            method='POST',
            files=files,
            api='beta',
        )
        log.debug(ret)
        log.debug(ret.text)
        log.debug('Update results:')
        log.debug(ret.json())

        ret = self.api(f'entitlements/{entitlement_id}', api='beta')
        try:
            log.debug(pretty_repr(ret.json()))
            return ret.json()
        except:
            log.error(ret.status_code)
            log.error(ret.text)
            return none

    def list_apps(self):
        """List all apps from IDN for the org (aka. Tennant)"""
        log.info('list_apps - start')
        ret = self.api('app/list?filter=org', api='cc')
        try:
            log.debug(pretty_repr(ret.json()))
            return ret.json()
        except:
            log.error(ret.status_code)
            log.error(ret.text)
            return none

    def get_ap(self, ap_id=None, ap_name=None):
        """Gets the Access Profile

        Dont confuse ap (access profile) with app (Application)

        Either ap_id or ap_name must be specified. If ap_name is specified
        there must be only a single ap that has that name, otherwise this
        will raise an exception.


        Parameters
        --------------------
        ap_id: string
            The ap ID that you want to fetch. You can use the ID as found
            from the list_aps method.

        ap_name: string
            The name of the ap that you want to fetch.  This search is case
            sensitive.

        Results
        --------------------
        ap: dict
            The access profile and its attributes

        """
        log.info(f'Getting Access Profile: {ap_name} - {ap_id}')

        if ap_name:
            get_aps = []
            log.debug(f'Searching for Acces Profile: {ap_name}')
            parameters = f'filters=name eq "{ap_name}"'

            ret = self.api(f'access-profiles?{parameters}', api='v3')
            get_aps = ret.json()

            num_found_aps = len(get_aps)

            if num_found_aps == 1:
                ap_id = get_aps[0]
                log.debug('Getting ap')
                return ap_id
            elif num_found_aps == 0:
                msg = f'Could not get ap {ap_name} - Not found'
                log.warning(msg)
                raise Exception(msg)
            elif num_found_aps > 1:
                msg = (
                    f'Could not get ap {ap_name} - Multiple aps with'
                    'this name were found'
                )
                log.error(msg)
                raise Exception(msg)

        if ap_id:
            ret = self.api(f'access-profiles/{ap_id}', api='v3')

            try:
                log.debug(pretty_repr(ret.json()))
                return ret.json()
            except:
                log.error(ret.status_code)
                log.error(ret.text)
                return None

        msg = 'get_ap requires ap_name or ap_id'
        log.error(msg)
        raise Exception(msg)

    def update_ap(self, ap_id, parameter, value):
        """Updates an Access Profile

        This updates an access profile.

        Parameters
        --------------------
        ap_id: string
            The ap ID that you want to update.

        parameter: string
            The parameter that you want to update.

        value: string
            The value you want to set.

        Results
        --------------------
        ap: dict
            The aplication and its attributes

        """
        log.info('update ap- start')

        payload = [
            {
                "op": "replace",
                "path": f"/{parameter}",
                "value": f"{value}",
            }
        ]
        log.debug(ap_id)
        log.debug(payload)

        patch_header = {'Content-Type': 'application/json-patch+json'}
        ret = self.api(
            f'access-profiles/{ap_id}',
            method='PATCH',
            payload=payload,
            headers=patch_header,
            api='beta',
        )

        try:
            log.debug(pretty_repr(ret.json()))
            return ret.json()
        except:
            log.error(ret.status_code)
            log.error(ret.text)
            return None

    def get_app(self, app_id=None, app_name=None):
        """Gets the App

        Dont confuse ap (access profile) with app (Application)

        Either app_id or app_name must be specified. If app_name is specified
        there must be only a single app that has that name, otherwise this
        will raise an exception.


        Parameters
        --------------------
        app_id: string
            The app ID that you want to fetch. You can use the ID as found
            from the list_apps method.

        app_name: string
            The name of the app that you want to fetch.  This search is case
            sensitive.

        Results
        --------------------
        app: dict
            The application and its attributes

        """
        log.info('get_app - start')

        if app_name:
            log.debug(f'Searching for app: [{app_name}]')
            get_apps = []
            for app in self.list_apps():
                name = app.get('name')
                # log.debug(f'Found app: [{name}] looking for [{app_name}]')
                if name == app_name:
                    log.debug('Found app to get based on name')
                    get_apps.append(app.get('id'))
            num_found_apps = len(get_apps)

            if num_found_apps == 1:
                app_id = get_apps[0]
                log.debug('Getting app')
            elif num_found_apps == 0:
                msg = f'Could not get app {app_name} - Not found'
                log.error(msg)
                raise Exception(msg)
            elif num_found_apps > 1:
                msg = (
                    f'Could not get app {app_name} - Multiple apps with'
                    'this name were found'
                )
                log.error(msg)
                raise Exception(msg)

        if app_id:
            ret = self.api(f'app/get/{app_id}', api='cc')

            try:
                log.debug(pretty_repr(ret.json()))
                return ret.json()
            except:
                log.error(ret.status_code)
                log.error(ret.text)
                return None

        msg = 'get_app requires app_name or app_id'
        log.error(msg)
        raise Exception(msg)

    def create_app(self, name, description):
        """Creates an Application

        This creates an Application.

        Parameters
        --------------------
        name: string
            The name of the application.

        description: string
            The description for the application.


        Results
        --------------------
        app: dict
            The application with its status

        """
        log.info('create_app - start')

        payload = {
            'name': name,
            'description': description,
            'appType': 'PASSWORD_MANAGEMENT_ONLY',
        }
        log.debug(payload)
        ret = self.api('app/create', method='POST', payload=payload, api='cc')
        try:
            log.debug(pretty_repr(ret.json()))
            return ret.json()
        except:
            log.error(ret.status_code)
            log.error(ret.text)
            return None

    def update_app(self, app_id, parameter, value):
        """Updates an Application

        This updates an Application.

        Parameters
        --------------------
        app_id: string
            The app ID that you want to fetch. You can use the ID as found
            from the list_apps method.

        parameter: string
            The parameter that you want to update. To update the name use
            alias instead.

        value: string
            The value you want to set.

        Results
        --------------------
        app: dict
            The application and its attributes

        """
        log.info('update app- start')

        payload = {
            parameter: value,
        }
        log.debug(payload)
        ret = self.api(
            f'app/update/{app_id}', method='POST', payload=payload, api='cc'
        )

        log.debug(ret)
        try:
            log.debug(pretty_repr(ret.json()))
            return ret.json()
        except:
            log.error(ret.status_code)
            log.error(ret.text)
            return None

    def delete_app(self, app_id=None, app_name=None):
        """Deletes an Application

        This deletes an Application.

        Parameters
        --------------------

        Either app_id or app_name must be specified. If app_name is specified
        there must be only a single app that has that name, otherwise this
        will raise an exception.

        app_id: string
            The appID of the application. NOTE: This uses the old cc API
            but this is NOT the short app app ID. (eg. 24016) You must list
            the app and then get the appId parameter from the app.

        app_name: string
            The name of the application.


        Results
        --------------------
        app: dict
            The application with its status

        """
        log.info('delete_app - start')

        if app_name:
            delete_apps = []
            for app in self.list_apps():
                name = app.get('name')
                if name == app_name:
                    log.debug('Found app to delete based on name')
                    delete_apps.append(app.get('appId'))
            num_del_apps = len(delete_apps)

            if num_del_apps == 1:
                app_id = delete_apps[0]
                log.debug('Deleting app')
            elif num_del_apps == 0:
                msg = f'Could not delete app {app_name} - Not found'
                log.error(msg)
                raise Exception(msg)
            elif num_del_apps > 1:
                msg = (
                    f'Could not delete app {app_name} - Multiple apps with'
                    'this name were found'
                )
                log.error(msg)
                raise Exception(msg)

        if app_id:
            ret = self.api(f'app/delete/{app_id}', method='POST', api='cc')

            try:
                log.debug(pretty_repr(ret.json()))
                return ret.json()
            except:
                log.error(ret.status_code)
                log.error(ret.text)
                return none

        msg = 'delete_app requires app_name or app_id'
        log.error(msg)
        raise Exception(msg)

    def get_app_owner(self, app_name):
        """Gets the Identity of the application owner

        Uses the search API to get the application owner. If you change the
        application owner, this can take some time to synchronize before it
        will appear here. The application owner can also be obtained by
        calling get_app, however this only gives you the short (cc) ID of the
        owner and not the full identity.

        Parameters
        --------------------
        app_name: string
            The name of the app that you want to fetch.

        Results
        --------------------
        owner_Identity: dict
            The Identity of the owner

        """
        log.info('get_app_owner - start')
        log.debug(f'getting app: {app_name}')
        payload = {
            "indices": ["identities"],
            "query": {
                "query": f'owns.apps.name:"{app_name}"',
            },
        }
        ret = self.api('search', method='POST', payload=payload, api='v3')

        # Using the ID there should only be one
        try:
            log.debug(pretty_repr(ret.json()))
            return ret.json()[0]
        except:
            log.error(ret.status_code)
            log.error(ret.text)
            return none

    def get_app_access_profiles(self, app_id):
        """Gets the access profiles for an app.
            This comes from the cc api app_id is the cc id

        Parameters
        --------------------
        app_id: string
            The app ID that you want to fetch the access profiles for. You
            can use the ID as found from the list_apps method.


        Results
        --------------------
        access_profiles: list of dicts
            The access profiles that are part of the application requested.

        """
        log.info('get_app - start')
        ret = self.api(f'app/getAccessProfiles/{app_id}', api='cc')

        try:
            log.debug(pretty_repr(ret.json()))
            return ret.json()['items']
        except:
            log.error(ret.status_code)
            log.error(ret.text)
            return None

    def search(self, payload):
        """Runs a generic search

        You must provide the full payload.

        Can be used to search for anything that the search accepts

        Tip: Use developer tools in your browser on the search screen to
        figure out the payload.

        For example:

        payload = {
            "query": {"query": "email:\"davep@fitchratings.com\""},
            "indices": ["identities"],
        }

        Parameters
        --------------------
        payload: dict
            The full search payload

        Results
        --------------------
        dict: the result
        """

        #        log.debug(payload)
        #        ret = self.api('search', method='POST', payload=payload)
        #        ids = ret.json()
        #        log.debug(str(ids))
        #        return ids
        offset = 0

        while True:
            ret = self.api(
                f'search?offset={offset}&limit=250',
                payload=payload,
                method='POST',
            )
            log.debug(ret)
            log.debug(ret.text)
            log.debug(ret.status_code)
            if ret.status_code == 200:
                results = ret.json()

                if len(results) == 0:
                    break

                for r in results:
                    offset += 1
                    yield (r)
            else:
                log.warning(ret.text)
                log.warning(ret.status_code)
                log.warning('Did not get 200 status_code - retrying')

    def get_user_by_email(self, email):
        """Gets the user by their email

        Search is case insensitive

        Parameters
        --------------------
        name: string
            The email to search

        Results
        --------------------
        identities: list of identities which match
        """

        payload = {
            "query": {"query": f"email:\"{email}\""},
            "indices": ["identities"],
        }

        # Until attributes are populated use personalEmail
        payload = {
            "query": {"query": f"attributes.activeDirectoryEmail\"{email}\""},
            "indices": ["identities"],
        }
        log.debug(payload)
        ret = self.api('search', method='POST', payload=payload)
        try:
            log.debug(pretty_repr(ret.json()))
            return ret.json()
        except:
            log.error(ret.status_code)
            log.error(ret.text)
            return None

    def get_user_by_name(self, name):
        """Gets the user by their name

        You can also include wildcards such as: Dave*
        Search is case insensitive

        Parameters
        --------------------
        name: string
            The name to search

        Results
        --------------------
        identities: list of identities
        """

        payload = {
            "query": {"query": f"displayName:\"{name}\""},
            "indices": ["identities"],
        }
        log.debug(payload)
        ret = self.api('search', method='POST', payload=payload)
        try:
            log.debug(pretty_repr(ret.json()))
            return ret.json()
        except:
            log.error(ret.status_code)
            log.error(ret.text)
            return None

    def get_user_by_id(self, user_id):
        """Gets the user by their ID

        Parameters
        --------------------
        user_id: string
            The users ID.

        Results
        --------------------
        identity: The Identity that matched
        """

        payload = {
            "query": {"query": f"id:\"{user_id}\""},
            "indices": ["identities"],
        }
        log.debug(payload)
        ret = self.api('search', method='POST', payload=payload)
        ids = ret.json()
        log.debug(str(ids))
        # there should be only one as we are searching on the ID itself
        return ids[0]

    def list_identity_profiles(self):
        """List identity profiles"""
        ret = self.api('identity_profiles', method='GET', api='beta')
        sources = ret.json()
        log.debug(str(sources))
        return sources

    def list_sources(self):
        """List all sources"""
        ret = self.api('sources', method='GET', api='beta')
        sources = ret.json()
        log.debug(str(sources))
        return sources

    def run_acct_aggregation(self, source_name, optimized=True):
        """Runs an account aggregation for a source

        Parameters
        --------------------
        source_name: string
            The name of the source to run the aggregation for.

        optimized: boolean
            If True this will be an optimized aggregation, if False it will
            do a non-optimized aggregation.

        Results
        --------------------
        dict: The result of the API call
        """
        disable_opt = optimized

        # Invert for the parameter in the API
        if disable_opt:
            disable_opt = 'false'
        else:
            disable_opt = 'true'

        cloud_id = self.get_sourceid_for_name(
            source_name, id_type='cloudExternalId'
        )
        log.debug(f'Running aggregation on cloudID: {cloud_id}')

        ret = self.api(
            f'source/loadAccounts/{cloud_id}?disableOptimization={disable_opt}',
            method='POST',
            api='cc',
        )
        try:
            log.debug(pretty_repr(ret.json()))
            return ret.json()
        except:
            log.error(ret.status_code)
            log.error(ret.text)
            return none

    def get_sourceid_for_name(self, name, id_type='id'):
        """Gets the source ID based on name of the source

        Parameters
        --------------------
        name: string
            The name of the source

        id_type: string
            The key of the specific ID you want to return. Type of ID to get,
            could be "id" or "cloudExternalId"

        Results
        --------------------
        id: string
            The ID

        """

        all_sources = self.api('sources').json()
        for s in all_sources:
            if s.get('name') == name:
                log.debug(pretty_repr(s))
                if id_type == 'id':
                    return s.get('id')
                else:
                    return s['connectorAttributes']['cloudExternalId']

    def update_approval(
        self,
        approval_id,
        new_owner=None,
        action='reject',
        reason='The approval has been reassigned',
    ):
        """Reassigns an approval to a different user

        Parameters
        --------------------
        approval_id: string
            The ID of the approval to reassign as retrieved from
            access-request_approvals

        action: string
            One of the following:

                approve - Approve an access request approval. Only the owner
                    of the approval and admin users are allowed to perform
                    this action.

                reject - Rejects an access request approval. Only the owner
                    of the approval and admin users are allowed to perform
                    this action.

                forward - Reassigns (Forwards) an access request approval to
                    a new owner. Only the owner of the approval and ORG_ADMIN
                    users are allowed to perform this action.


        new_owner: string
            The ID of the person who the approval will be reassigned to. Only
            used if action is "forward".

        Results
        --------------------
        ret: 202 is success anything else you better check


        """

        payload = {
            'comment': reason,
        }

        if action == 'forward':
            payload = {
                'newOwnerId': new_owner,
            }

        ret = self.r(
            f'access-request-approvals/{approval_id}/{action}',
            method='POST',
            payload=payload,
            api='v3',
        )
        # print(ret.json())
        log.debug(ret)
        return ret


if __name__ == '__main__':
    pass

import requests
import os
import logging
import json

log = logging.getLogger(__name__)

dir_path = os.path.dirname(os.path.realpath(__file__))
cert_path = os.path.join(dir_path, 'certificates')

# should we just add this to the system cert path
# Zsacler is a mitm
if os.path.exists(cert_path):
    zscaler_cert_file = os.path.join(cert_path, 'Zscaler_root_CA.cer')
else:
    zscaler_cert_file = None


class IDNApi:
    def __init__(self, secret=None, client_id=None, tenant=None):
        # If the API settings didn't come from instantiation then get from
        # config
        if not (secret and client_id and tenant):
            (secret, client_id, tenant) = self.get_api_config()

        if not (secret and client_id and tenant):
            # If we still don't have it, then raise an error
            msg = 'IDNApi - Missing API key and tenant information'
            log.error(msg)
            raise Exception(msg)

        self.tenant = tenant
        url = (
            f'https://{tenant}.api.identitynow.com/oauth/token?grant_type'
            f'=client_credentials&client_id={client_id}'
            f'&client_secret={secret}'
        )

        # log.info(f'curl --request POST --url {url}')
        if zscaler_cert_file:
            x = requests.post(url, verify=zscaler_cert_file)
        else:
            x = requests.post(
                url,
                #            proxies=dict(
                #                http='socks5://localhost:8888',
                #                https='socks5://localhost:8888'
                #            ),
            )

        # log.info(x.json())
        self.token = x.json().get('access_token', None)

    def get_api_config(self):
        try:
            config_file = os.path.join(os.path.expanduser('~'), '.idn_api')
            with open(config_file, "r") as f:
                api_config = json.load(f)
                secret = api_config.get('secret', None)
                client_id = api_config.get('client_id', None)
                tenant = api_config.get('tenant', None)
                return (secret, client_id, tenant)
        except Exception as e:
            msg = f'Could not load API config from {config_file}'
            log.error(msg)
            log.error(e)
            return (None, None, None)

    def r(
        self,
        endpoint,
        method='GET',
        params=[],
        payload=None,
        headers={},
        files=None,
        api='v3',
    ):
        """
        r - Request something from the API
        """

        if api == 'cc':
            url = (
                f'https://{self.tenant}.api.identitynow.com/cc/api/{endpoint}'
            )
        else:
            # cc format is. . .
            url = f"https://{self.tenant}.api.identitynow.com/{api}/{endpoint}"

        default_headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.token}',
        }
        default_headers.update(headers)
        log.debug(default_headers)
        log.debug(f'URL: {url}')
        # quit()

        if zscaler_cert_file:
            response = requests.request(
                method,
                url,
                headers=default_headers,
                files=files,
                verify=zscaler_cert_file,
                json=payload,
            )
        else:
            response = requests.request(
                method,
                url,
                headers=default_headers,
                files=files,
                json=payload,
                #            proxies=dict(
                #                http='socks5://localhost:8888',
                #                https='socks5://localhost:8888'
                #            ),
            )
        #        log.info(response)
        #        log.info(response.text)
        #        log.info(response.json())
        return response


def set_disableOrderingCheck(api, source_id):
    """
    set_disableOrderingCheck

    sets disableOrderingCheck attribute on a connector

    see:
    https://support.sailpoint.com/csm?id=kb_article_view&sys_kb_id=30af1be4972c6d14d7557f1ef053afd8

    """
    payload = [
        {
            'op': 'add',
            'path': '/connectorAttributes/disableOrderingCheck',
            'value': True,
        }
    ]
    headers = {'Content-Type': 'application/json-patch+json'}
    ret = api.r(
        f'sources/{source_id}',
        method='PATCH',
        headers=headers,
        payload=payload,
    )
    log.info(ret)
    log.info(ret.text)
    log.info(ret.json())


if __name__ == '__main__':
    quit()
    api = IDNApi()
    # api.r('public-identities')
    # api.r('accounts')
    # api.r('identities', method='POST')

    #    # Get connector rules
    #    ret = api.r(f'connector-rules', api='beta')
    #    log.info(ret)
    #    quit()

    # ret = api.r('sources')
    # log.info(ret.json())

    #    # RAC Module
    #    source_id = '953af34c11f54e59ad55ca0fb0ded417'
    #    set_disableOrderingCheck(api, source_id)

    quit()

    # Get connector rule by ID
    connector_rule = 'fa488de1772f4059b8cd81bdf1940de6'
    ret = api.r(f'connector-rules/{connector_rule}', api='beta')
    log.info(ret)
    # log.info the source code for the connector rule
    ret_json = ret.json()
    source = ret_json['sourceCode']['script']
    log.info(f'{source}')
    quit()

    # Transforms
    ret = api.r('transforms', api='v3')
    log.info(ret.json())
    quit()

    # Get provisioning policies
    some_id = '26820'  # cloud ID
    some_id = '50fc360f905543f9bd681a2e6b45169f'  # just the id
    ret = api.r(f'sources/{some_id}/provisioning-policies/CREATE', api='beta')
    log.info(ret)
    quit()

    ret = api.r('sources')
    log.info(ret)
    quit()

    # 26821 - GWC
    #    api.r('IdentityAttribute/list', api='cc')

    # Non optimized aggregation
    #     api.r(
    #         'source/loadAccounts/26820?disableOptimization=true
    #         method='POST',
    #         api='cc',
    #     )

    # Transforms
    ret = api.r('transforms/428e5ce0-c9f7-45e2-b6af-642d36057dfe', api='v3')
    log.info(ret)
    quit()

    # Access Profiles
    ret = api.r('access-profiles', api='beta')
    log.info(ret)
    quit()

    # Governance groups API
    # https://developer.sailpoint.com/discuss/t/rest-apis-for-managing-governance-groups/925
    ret = api.r('workgroups', api='v2')
    log.info(ret)

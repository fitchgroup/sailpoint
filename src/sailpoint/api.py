import requests
import os
import logging
import json
import time

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

        # log.debug(f'curl --request POST --url {url}')
        if zscaler_cert_file:
            x = requests.post(url, verify=zscaler_cert_file, timeout=10)
        else:
            x = requests.post(
                url,
                timeout=10
                #            proxies=dict(
                #                http='socks5://localhost:8888',
                #                https='socks5://localhost:8888'
                #            ),
            )

        # log.debug(x.json())
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
            - Will only return top 250 max
            - You can pass offset and limit manually as part of the endpoint
              string to overcome this
        """
        if api not in ['beta', 'v3']:
            log.warning(f'Using deprecated API: {api} - {endpoint}')

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
        # log.debug(default_headers)
        log.debug(f'URL: {url}')
        # quit()

        if zscaler_cert_file:
            for _ in range(5):  # try up to 5 times
                try:
                    response = requests.request(
                        method,
                        url,
                        headers=default_headers,
                        files=files,
                        verify=zscaler_cert_file,
                        json=payload,
<<<<<<< HEAD
                        timeout=20,
=======
>>>>>>> main
                    )
                    break
                except Exception as e:
                    log.error(e)
                    log.error('Sleeping 300ms and trying again up to 5 times')
                    time.sleep(300 / 1000)  # sleep for 300ms
                    pass
        else:
            for _ in range(5):  # try up to 5 times
                try:
                    response = requests.request(
                        method,
                        url,
                        headers=default_headers,
                        files=files,
                        json=payload,
<<<<<<< HEAD
                        timeout=20,
=======
>>>>>>> main
                    )
                    break
                except Exception as e:
                    log.error(e)
                    log.error('Sleeping 300ms and trying again up to 5 times')
                    time.sleep(300 / 1000)  # sleep for 300ms
                    pass
<<<<<<< HEAD
        # log.debug(response)
        # log.debug(response.text)
=======
        log.debug(response)
        log.debug(response.text)
>>>>>>> main
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
    log.debug(ret)
    log.debug(ret.text)
    log.debug(ret.json())


if __name__ == '__main__':
    pass

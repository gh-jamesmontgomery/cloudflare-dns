from libcloud.dns.types import Provider, RecordType
from libcloud.dns.providers import get_driver
from datetime import datetime
import getpass

print("--BEGIN--")
cls = get_driver(Provider.CLOUDFLARE)
apiKey = getpass.getpass()
cfUsername = 'your-cf-user-id'
#Authenticate
driver = cls(cfUsername, apiKey)

zones = driver.list_zones()

print(f'{len(zones)} zone(s) found')

for zone in zones:
    print(zone.id,zone.domain)

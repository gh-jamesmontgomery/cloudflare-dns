import json
import boto3
import os
import decimal
from datetime import datetime

from libcloud.dns.types import Provider, RecordType
from libcloud.dns.providers import get_driver

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if abs(o) % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

def raise_(ex):
    raise ex

def lambda_handler(event, context):
    cls = get_driver(Provider.CLOUDFLARE)
    p = os.environ['cf-API-key']
    driver = cls('cf-user-id', p)
    
    dynamodb = boto3.resource('dynamodb',region_name='region-name')
    table = dynamodb.Table('tablename')

    zone = driver.get_zone(zone_id='cf-zone-id')
    records = zone.list_records()
    recordCount = len(records)
    
    print(f'{recordCount} records found')
    
    #A min and max threshold are supplied upon invocation. Anything less or more is unexpected and so we stop.
    if recordCount < event['minRecords']:
        errorMessage = f'min records not met, count = {recordCount}'
        raise_(Exception(errorMessage))
    elif recordCount > event['maxRecords']:
        errorMessage = f'max records exceeded , count = {recordCount}'
        raise_(Exception(errorMessage))
    
    #Determine now and future expiry date of this record    
    thisTime = datetime.now()
    lastSeenEpoch = int(thisTime.timestamp())
    
    oneWeekInSeconds = 604800
    expireInWeeks = 1
    
    expireOn = lastSeenEpoch + (oneWeekInSeconds*expireInWeeks)

    for thisRecord in records:
        thisCfRecordID = thisRecord.id
        thisCfModifiedOn = thisRecord.extra['modified_on']
        thisType = thisRecord.type

        if thisRecord.name is None:
            thisName = 'not applicable'
        else:
            thisName = thisRecord.name
            
        thisData = thisRecord.data
        thisProxied = thisRecord.extra['proxied']
        thisTimeToLive = thisRecord.ttl
        thisPriority = thisRecord.extra['priority']
        
        response = table.put_item(Item = {
        'cf_record_id': thisCfRecordID,
        'cf_modified_on': thisCfModifiedOn,
        'type': thisType,
        'name': thisName,
        'data': thisData,
        'ttl': thisTimeToLive,
        'proxied': thisProxied,
        'priority': thisPriority,
        'last_seen': lastSeenEpoch,
        'expireOn': expireOn
        }
        )

    return {
        'statusCode': 200,
        'body': json.dumps('Function has ended')
    }

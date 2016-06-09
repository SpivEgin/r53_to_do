#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import boto3
import click
import requests


DIGITAL_OCEAN_KEY = os.environ.get('DIGITAL_OCEAN_KEY')


def do(method, path, **kwargs):
    url = 'https://api.digitalocean.com/v2/' + path
    headers = kwargs.get('headers', {})
    headers['Authorization'] = 'Bearer {}'.format(DIGITAL_OCEAN_KEY)

    print(url, kwargs)

    if method == 'post':
        response = requests.post(url, headers=headers, **kwargs)

    elif method == 'get':
        response = requests.get(url, headers=headers, **kwargs)

    elif method == 'delete':
        response = requests.delete(url, headers=headers)
        return response.status_code == 204

    if response.status_code == 204:
        return True

    return response.json()


@click.command()
@click.argument('domain', nargs=1, required=True)
@click.option('--aws-profile', type=str)
def r53_to_do(domain, aws_profile):
    if aws_profile:
        session = boto3.session.Session(profile_name=aws_profile)
    else:
        session = boto3.session.Session()

    r53 = session.client('route53')
    response = r53.list_hosted_zones_by_name(DNSName=domain)

    try:
        zone = [x for x in response['HostedZones'] if x['Name'] == domain + '.'][0]
    except IndexError:
        print("Couldn't find {} in your hosted zones:\n{}".format(domain, ', '.join(
            [x['Name'][:-1] for x in response['HostedZones']]))
        )
        return

    default_ip = ''
    record_sets = r53.list_resource_record_sets(HostedZoneId=zone['Id'])['ResourceRecordSets']
    for record in record_sets:
        print('{}\t{}\t{}'.format(
            record['Type'], record['Name'],
            ' '.join([x['Value'] for x in record['ResourceRecords']])
        ))
        if record['Type'] == 'A' and record['Name'] == domain + '.':
            default_ip = record['ResourceRecords'][0]['Value']

    if not default_ip:
        print("There is no default A record, we can't create a domain on DO without one")
        return

    print('The default IP for this record will be set to {}'.format(default_ip))

    # get domains
    domain_response = do('get', 'domains/{}'.format(domain))

    if 'id' in domain_response and domain_response['id'] == 'not_found':
        response = do('post', 'domains', json={'name': domain, 'ip_address': default_ip})
        print(response)
    else:
        print('Looks like the domain already exists, go delete it manually then continue')
        return

    # TODO: Review how this part works
    for record in record_sets:
        if record['Type'] not in ['A', 'CNAME', 'MX', 'TXT', 'SPF']:
            print(record['Type'], "is not a supported DNS record type")
            continue
        for resource in record['ResourceRecords']:
            request_data = {}
            value = resource['Value']
            if record['Type'] == 'MX':
                priority, value = value.split()
                request_data['priority'] = priority

            if '.{}.'.format(domain) in value:
                value = value.replace('.{}.'.format(domain), '')

            if record['Type'] in ['CNAME', 'MX'] and '.' not in value[-1]:
                request_data['data'] = '{}.'.format(value)
            else:
                request_data['data'] = value

            # This code snipet deals with escaping strings (eg. converting \\052 into *)
            # This snippet isn't full proof
            if record['Type'] == 'A' and '\\' in record['Name']:
                record['Name'] = record['Name'].decode('string_escape')

            # Digital ocean uses TXT types for all SPF enteries
            if record['Type'] == 'SPF':
                record['Type'] = 'TXT'

            request_data['type'] = record['Type']
            request_data['name'] = record['Name'][:-1]

            response = do('post', 'domains/{}/records'.format(domain), json=request_data)
            print(response)


if __name__ == '__main__':
    r53_to_do()

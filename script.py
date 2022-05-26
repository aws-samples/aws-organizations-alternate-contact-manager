# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import json
import logging
import time
from simple_term_menu import TerminalMenu
from botocore.exceptions import ClientError
from datetime import datetime
from pprint import pprint


def list_accounts_func():
    list_of_accounts_id = []
    list_of_accounts = boto3.client(
        'organizations').list_accounts()['Accounts']
    for account in list_of_accounts:
        list_of_accounts_id.append(str(account["Id"]))
    return list_of_accounts_id


def get_account_id():
    return boto3.client('sts').get_caller_identity()['Account']


def list_func(accounts, current_account_id, menu_entry_1_list):
    resp = {'AlternateContact': {}}
    client = boto3.client('account')

    for x in accounts:
        alternate_contact_type = {}
        for y in menu_entry_1_list:
            print('Getting ' + y + ' alternate contact for ' + x + '...')
            try:
                if x == current_account_id:
                    resp_alternate_contact = client.get_alternate_contact(
                        AlternateContactType=y.upper())
                    resp_alternate_contact['AlternateContact'].pop(
                        'AlternateContactType')
                else:
                    resp_alternate_contact = client.get_alternate_contact(
                        AccountId=str(x), AlternateContactType=y.upper())
                    resp_alternate_contact['AlternateContact'].pop(
                        'AlternateContactType')
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    resp_alternate_contact = {}
                    resp_alternate_contact['AlternateContact'] = 'Null'
                else:
                    print('\n')
                    logging.error(e)
                    return False
            alternate_contact_type[y] = resp_alternate_contact['AlternateContact']
        resp['AlternateContact'][x] = alternate_contact_type

    export_to_s3 = input(
        '\nDo you want to export the result to an S3 bucket? (y/n): ')
    if export_to_s3 == 'y':
        s3_bucket_name = input('S3 bucket name: ')
        s3_object_name = 'alternate-contact-list_' + \
            datetime.now().strftime("%d-%m-%Y_%H-%M-%S") + '.json'
        s3_client = boto3.client('s3')
        try:
            s3_client.put_object(
                Body=bytes(json.dumps(resp).encode('UTF-8')),
                Bucket=s3_bucket_name,
                Key=s3_object_name
            )
        except ClientError as e:
            print('\n')
            logging.error(e)
            print(e)
            return False
        return True
    elif export_to_s3 == 'n':
        print('\nReturn: \n')
        pprint(resp['AlternateContact'])
        return True
    else:
        print('\nInvalid input.')
        return False


def update_func(accounts, current_account_id, menu_entry_1_list):
    client = boto3.client('account')

    email_address = input(
        'Type the email address (see the README.md file to valid patterns): ')
    name = input('Type the name (see the README.md file to valid patterns): ')
    phone_number = input(
        'Type the phone number (see the README.md file to valid patterns): ')
    title = input(
        'Type the title (see the README.md file to valid patterns): ')
    print('\n')

    for x in accounts:
        for y in menu_entry_1_list:
            print('Updating ' + y + ' alternate contact for ' + x + '...')
            if current_account_id == x:
                try:
                    client.put_alternate_contact(
                        AlternateContactType=y.upper(),
                        EmailAddress=email_address,
                        Name=name,
                        PhoneNumber=phone_number,
                        Title=title
                    )
                except ClientError as e:
                    print('\n Could not update ' + y +
                          ' alternate contact for ' + x + '... Error: ' + str(e))
                    logging.error(e)
                    return False
            else:
                try:
                    client.put_alternate_contact(
                        AccountId=x,
                        AlternateContactType=y.upper(),
                        EmailAddress=email_address,
                        Name=name,
                        PhoneNumber=phone_number,
                        Title=title
                    )
                except ClientError as e:
                    print('\n Could not update ' + y +
                          ' alternate contact for ' + x + '... Error: ' + str(e))
                    logging.error(e)
                    return False
    return True


def delete_func(accounts, current_account_id, menu_entry_1_list):
    client = boto3.client('account')

    for x in accounts:
        for y in menu_entry_1_list:
            print('Deleting ' + y + ' alternate contact for ' + x + '...')
            if current_account_id == x:
                try:
                    client.delete_alternate_contact(
                        AlternateContactType=y.upper()
                    )
                except ClientError as e:
                    print('\n Could not delete ' + y +
                          ' alternate contact for ' + x + '... Error: ' + str(e))
                    logging.error(e)
                    return False
            else:
                try:
                    client.delete_alternate_contact(
                        AccountId=x,
                        AlternateContactType=y.upper()
                    )
                except ClientError as e:
                    print('\n Could not delete ' + y +
                          ' alternate contact for ' + x + '... Error: ' + str(e))
                    logging.error(e)
                    return False
    return True


def main():
    bold = '\033[1m'
    italic = '\033[0;3m'
    regular = '\033[0;0m'
    print(bold + '\nAlternate Contacts Manager')
    print(italic + 'Solution developed for batch management of alternate contacts. For more information, visit: https://github.com/aws-samples/alternate-contact-manager\n\n' + regular)

    options_0 = ['List', 'Update', 'Delete']
    terminal_menu_0 = TerminalMenu(options_0)
    menu_entry_index_0 = terminal_menu_0.show()
    menu_entry_0 = options_0[menu_entry_index_0]
    print('Action: ' + options_0[menu_entry_index_0])

    if options_0[menu_entry_index_0] == 'Delete':
        accounts = input(
            'Account ID (delete action allowed for one account at a time): ')
        accounts = accounts.split(',')
    else:
        accounts = input(
            'Account IDs(enter a list of account ids separated by comma / all): ')
        if accounts == 'all':
            accounts = list_accounts_func()
        else:
            accounts = accounts.replace(' ', '')
            accounts = accounts.split(',')

    for x in accounts:
        if len(x) != 12:
            print("\nAccount ID " + str(x) +
                  " is not a valid AWS Account ID.\n")
            exit()
        else:
            aws_org_accounts = list_accounts_func()
            if x not in aws_org_accounts:
                print("\nAccount ID " + str(x) +
                      " does not belong to your AWS Organization.\n")
                exit()
            else:
                pass

    current_account_id = get_account_id()

    options_1 = ['Billing', 'Operations', 'Security', 'All']
    terminal_menu_1 = TerminalMenu(options_1)
    menu_entry_index_1 = terminal_menu_1.show()
    print('Alternate contact type: ' + options_1[menu_entry_index_1] + '\n')
    if options_1[menu_entry_index_1] == 'All':
        menu_entry_1_list = ['Billing', 'Operations', 'Security']
    else:
        menu_entry_1_list = [options_1[menu_entry_index_1]]

    tic = time.perf_counter()

    if menu_entry_0 == 'List':
        resp = list_func(accounts, current_account_id, menu_entry_1_list)
    elif menu_entry_0 == 'Update':
        resp = update_func(accounts, current_account_id, menu_entry_1_list)
    else:
        resp = delete_func(accounts, current_account_id, menu_entry_1_list)

    toc = time.perf_counter()

    print(f'\nCompleted successfully in {toc - tic:0.4f} seconds!\n') if resp == True else print(
        '\nERROR: somethig went wrong.\n')


if __name__ == '__main__':
    main()

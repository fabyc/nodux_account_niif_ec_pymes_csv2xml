#!/usr/bin/python
# -*- coding: UTF-8 -*-
from lxml import etree
import csv
import re

account_ids = []


def compute_code(account_id):
    if 'pymes' in account_id:
        code = account_id.replace('pgc_pymes_', '')
    else:
        code = account_id.replace('pgc_', '')
    code = code[:-2] + '%' + code[-2:]
    return code


def compute_parent(account_id):
    parent_id = account_id
    while parent_id not in account_ids:
        parent_id = parent_id[:-1]
        if not parent_id:
            print "Account parent of %s not found." % account_id
            break
    return parent_id


def get_csv_reader(file_name):
    try:
        reader = csv.reader(open(file_name, 'rU'), delimiter=str(','),
                            quotechar=str('"'))
    except:
        print ("Error reading %s csv file" % file_name)
        return []
    return reader


def init_xml():
    xml = etree.Element('tryton')
    xml_data = etree.SubElement(xml, 'data')
    return xml, xml_data


def write_xml_file(xml, xml_data, target_file):
    xml_data = etree.ElementTree(xml)
    xml_data.write(target_file, encoding='UTF-8', method='xml',
        standalone=False, pretty_print=True)


def set_record(xml_data, record):

    def set_subelement(parent_xml_element, label, attrib, text=False):
        xml_element = etree.SubElement(parent_xml_element, label,
                                       attrib=attrib)
        if text:
            xml_element.text = text.decode('utf-8')
        return xml_element

    attrib = {
        'model': record['model'],
        'id': record['id'],
    }
    xml_record = set_subelement(xml_data, 'record', attrib)
    for field in record['fields']:
        text = False
        attrib = {'name': field['name']}
        if 'eval' in field and field.get('eval'):
            attrib.update({'eval': field['eval']})
        elif 'ref' in field and field.get('ref'):
            attrib.update({'ref': field['ref']})
        elif 'text' in field and field.get('text'):
            text = field['text']
        else:
            continue
        set_subelement(xml_record, 'field', attrib, text)


def set_records(xml_data, records):
    for record in records:
        set_record(xml_data, record)


def create_account_types(xml_data, file_name):
    # Read account_type csv file
    reader = get_csv_reader(file_name)
    for row in reader:
        if reader.line_num == 1:
            continue
        record = {
            'model': 'account.account.type.template',
            'id': row[0],
            'fields': [
                {'name': 'name', 'text': row[1]},
                {'name': 'parent', 'ref': row[3]},
                {'name': 'sequence', 'eval': row[2]},
                {'name': 'balance_sheet', 'eval': row[5]},
                {'name': 'income_statement', 'eval': row[6]},
                {'name': 'display_balance', 'text': row[4]},
            ],
        }
        set_record(xml_data, record)


def create_accounts(xml_data, file_name):
    # Read account_csv file
    reader = get_csv_reader(file_name)
    for row in reader:
        if reader.line_num == 1:
            continue
        record = {
            'model': 'account.account.template',
            'id': row[0],
            'fields': [
                {'name': 'name', 'text': row[1]},
                {'name': 'parent', 'ref': row[3]},
                {'name': 'code', 'text': row[2]},
                {'name': 'reconcile', 'eval': row[6]},
                {'name': 'kind', 'text': row[4]},
                {'name': 'type', 'ref': row[5]},
                {'name': 'deferral', 'eval': row[7]},
                {'name': 'party_required', 'eval': row[8]},
            ],
        }
        set_record(xml_data, record)
        account_ids.append(record['id'])


def create_tax_groups(xml_data, file_name):
    # Read tax_group csv file
    reader = get_csv_reader(file_name)
    for row in reader:
        if reader.line_num == 1:
            continue
        record = {
            'model': 'account.tax.group',
            'id': row[0],
            'fields': [
                {'name': 'name', 'text': row[1]},
                {'name': 'code', 'text': row[2]},
                {'name': 'kind', 'text': row[3]},
            ],
        }
        set_record(xml_data, record)


def create_tax_codes(xml_data, file_name):
    # Read tax_code csv file
    reader = get_csv_reader(file_name)
    for row in reader:
        if reader.line_num == 1:
            continue
        record = {
            'model': 'account.tax.code.template',
            'id': row[0],
            'fields': [
                {'name': 'name', 'text': row[1]},
                {'name': 'parent', 'ref': row[3]},
                {'name': 'code', 'text': row[2]},
                {'name': 'account', 'ref': row[4]},
            ],
        }
        set_record(xml_data, record)


def create_taxes(xml_data, file_names):
    for file_name in file_names:
        records = read_tax_file(file_name)
        for record in records:
            if record['fields'][len(record['fields']) - 1]['name'] == \
                    'account_name':
                record['fields'].pop()
            set_record(xml_data, record)


def read_tax_file(file_name):
    # Read tax csv file
    reader = get_csv_reader(file_name)
    records = []
    for row in reader:
        if reader.line_num == 1:
            continue
        rate = row[6]
        regex = re.compile("^Decimal\('(.*)'\)$")
        r = regex.search(rate)
        if r:
            value, = r.groups()
            rate = 'Decimal(\'%s\')' % str(float(value) / 100.0)
        tax_record = {
            'model': 'account.tax.template',
            'id': row[0],
            'fields': [
                {'name': 'name', 'text': row[1]},
                {'name': 'description', 'text': row[1]},
                {'name': 'parent', 'ref': row[2]},
                {'name': 'account', 'ref': row[4]},
                {'name': 'group', 'ref': row[3]},
                {'name': 'type', 'text': row[5]},
                {'name': 'rate', 'eval': rate},
                {'name': 'invoice_account', 'ref': row[7]},
                {'name': 'credit_note_account', 'ref': row[8]},
                {'name': 'invoice_base_code', 'ref': row[9]},
                {'name': 'invoice_tax_code', 'ref': row[10]},
                {'name': 'credit_note_base_code', 'ref': row[11]},
                {'name': 'credit_note_tax_code', 'ref': row[12]},
                {'name': 'invoice_base_sign', 'eval': row[13]},
                {'name': 'invoice_tax_sign', 'eval': row[14]},
                {'name': 'credit_note_base_sign', 'eval': row[15]},
                {'name': 'credit_note_tax_sign', 'eval': row[16]},
                {'name': 'sequence', 'text': row[17]},
            ],
        }
        if len(row) >= 19:
            tax_record['fields'].append({
                    'name': 'report_description', 'text': row[18]})
        records.append(tax_record)
    return records


def create_tax_accounts(account_xml_data, file_names):
    records = []
    for file_name in file_names:
        records.extend(read_tax_file(file_name))

    for re_record in records:
        record = {
            'model': 'account.account.template',
            'fields': [],
        }
        for field in re_record['fields']:
            if field['name'] == 'invoice_account':
                record['id'] = field['ref']
                if record['id'] in account_ids:
                    break
                parent = compute_parent(field['ref'])
                record['fields'].extend([
                    {'name': 'code', 'text': compute_code(field['ref'])},
                    {'name': 'parent', 'ref': parent},
                ])
                account_type = 'co_balance_22207'
                kind = 'other'
            elif field['name'] == 'account_name':
                record['fields'].extend([
                    {'name': 'name', 'text': field['text']},
                ])
        record['fields'].extend([
            {'name': 'reconcile', 'eval': 'True'},
            {'name': 'kind', 'text': kind},
            {'name': 'type', 'ref': account_type},
            {'name': 'deferral', 'eval': 'True'},
            {'name': 'party_required', 'eval': 'True'},
        ])
        if record['id'] not in account_ids:
            set_record(account_xml_data, record)
            account_ids.append(record['id'])


def normalize_xml(archive):
    data = ''
    for line in open(archive):
        spaces = 0
        char = line[0]
        while char == ' ':
            spaces += 1
            char = line[spaces]
        spaces *= 2
        line = line.strip()
        if "encoding='UTF-8'" in line:
            line = (line.replace("encoding='UTF-8'", '').
                    replace("standalone='no'", '').replace('  ?', '?'))
            line += ('\n<!-- This file is part of Tryton.  The COPYRIGHT file '
                'at the top level of\nthis repository contains the full '
                'copyright notices and license terms. -->')
            data += ' ' * spaces + line + '\n'
        elif 'tryton' in line or 'data' in line:
            data += ' ' * spaces + line + '\n'
        else:
            line = line.strip('<>')
            if '">' not in line and '</' not in line:
                ends_label = False
                if line[-1] == '/':
                    ends_label = True
                    line = line.strip('/')
                model_attr = 0
                id_attr = 0
                name_attr = 0
                ref_attr = 0
                eval_attr = 0
                words = line.split()
                for word in words:
                    if 'model' in word:
                        model_attr = words.index(word)
                    elif 'id' in word:
                        id_attr = words.index(word)
                    elif 'name' in word:
                        name_attr = words.index(word)
                    elif 'ref' in word:
                        ref_attr = words.index(word)
                    elif 'eval' in word:
                        eval_attr = words.index(word)
                if id_attr and model_attr > id_attr:
                    words[id_attr], words[model_attr] = (
                        words[model_attr], words[id_attr])
                elif ref_attr and name_attr > ref_attr:
                    words[ref_attr], words[name_attr] = (
                        words[name_attr], words[ref_attr])
                elif eval_attr and name_attr > eval_attr:
                    words[eval_attr], words[name_attr] = (
                        words[name_attr], words[eval_attr])
                if ends_label:
                    line = '<' + ' '.join([w for w in words]) + '/>'
                else:
                    line = '<' + ' '.join([w for w in words]) + '>'
            else:
                line = '<' + line + '>'
            data += ' ' * spaces + line + '\n'
    return data


if __name__ == '__main__':
    # Create xml standard files
    # Initialize xml etree.Elements for each file
    account_xml, account_xml_data = init_xml()
    tax_xml, tax_xml_data = init_xml()
    account_pyme_xml, account_pyme_xml_data = init_xml()
    
    # Next add data to each xml etree.Element
    # First to account_xml etree.Element
    
    # Full Chart Account
    create_account_types(account_xml_data, '01-account_types.csv')
    print "01-account_types.csv"
    create_accounts(account_xml_data, '02-accounts.csv')
    print "02-accounts.csv"
    create_accounts(account_xml_data, '03-tax_accounts.csv')
    print "03-tax_accounts.csv"

    # Pyme Chart Account
    #create_account_types(account_pyme_xml_data, 'account_types.csv')
    #create_accounts(account_pyme_xml_data, 'accounts_pyme.csv')
    #create_accounts(account_pyme_xml_data, 'tax_accounts.csv')
    
    # TODO: Create accounts automatic from template taxes
    #create_tax_accounts(account_xml_data, ['taxes_accounts.csv'])

    # And then to tax_xml etree.Element
    create_tax_groups(tax_xml_data, '06-tax_groups.csv')
    print "06-tax_groups.csv"
    create_tax_codes(tax_xml_data, '04-tax_codes.csv')
    print "04-tax_codes.csv"
    create_taxes(tax_xml_data, ['05-taxes.csv'])
    print "05-taxes.csv"

    # Finally save each xml etree.Element to a file
    write_xml_file(account_xml, account_xml_data, 'company_charts/account_ec_pymes.xml')
    write_xml_file(tax_xml, tax_xml_data, 'company_charts/tax_ec_pymes.xml')
    #write_xml_file(account_pyme_xml, account_pyme_xml_data, 'company_charts/account_pyme.xml')

    archives = (
        'company_charts/account_ec_pymes.xml',
        'company_charts/tax_ec_pymes.xml',
        #'company_charts/account_pyme.xml',
    )
    for archive in archives:
        data = normalize_xml(archive)
        with open(archive, 'w') as f:
            f.write(data)
